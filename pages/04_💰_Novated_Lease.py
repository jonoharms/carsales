import streamlit as st
from attrs import define, asdict, field
import flatdict
import numpy_financial as npf
import pandas as pd
from decimal import Decimal, getcontext, ROUND_HALF_DOWN
from numbers import Number


def D(num, prec='0.01'):
    return Decimal(num).quantize(Decimal(prec), rounding=ROUND_HALF_DOWN)


RESIDUAL = {
    1: D(65.63),
    2: D(56.25),
    3: D(46.88),
    4: D(37.50),
    5: D(28.13),
}


def spaced_line(name: str, number: D):
    spaces = 40 - len(name)
    return '**' + name + ':**' + '&nbsp;' * spaces + f'{number:,.2f}'


@define
class Car:
    make: str
    model: str
    base_price_ex_gst: Decimal
    accessories_price_ex_gst: Decimal
    delivery_charges_ex_gst: Decimal
    stamp_duty: Decimal

    total_price_inc_gst: Decimal = field(init=False)
    drive_away_price: Decimal = field(init=False)
    total_price_ex_gst: Decimal = field(init=False)
    gst: Decimal = field(init=False)

    def __attrs_post_init__(self):
        self.total_price_ex_gst = D(
            sum(
                [
                    self.base_price_ex_gst,
                    self.accessories_price_ex_gst,
                    self.delivery_charges_ex_gst,
                ]
            )
        )
        self.gst = self.total_price_ex_gst * D(0.1)
        self.total_price_inc_gst = D(self.total_price_ex_gst + self.gst)
        self.drive_away_price = D(self.total_price_inc_gst + self.stamp_duty)


@define
class NovatedLease:
    car: Car
    interest_rate: Decimal
    lease_term: int
    name: str = field(init=False)
    financed_amount: Decimal = field(init=False)
    residual_amount_ex_gst: Decimal = field(init=False)
    residual_amount_inc_gst: Decimal = field(init=False)
    monthly_repayment: Decimal = field(init=False)
    annual_repayment: Decimal = field(init=False)
    total_purchase_cost: Decimal = field(init=False)

    def __attrs_post_init__(self):
        self.financed_amount = (
            self.car.total_price_ex_gst + self.car.stamp_duty
        )
        self.residual_amount_ex_gst = D(
            self.financed_amount * RESIDUAL[self.lease_term] / 100
        )
        self.residual_amount_inc_gst = D(
            D(self.residual_amount_ex_gst) * D(1.1)
        )
        self.monthly_repayment = D(
            npf.pmt(
                float(self.interest_rate) / 12,
                self.lease_term * 12,
                -(
                    float(self.financed_amount)
                    - float(self.residual_amount_ex_gst)
                ),
            )
            + float(self.residual_amount_ex_gst)
            * float(self.interest_rate)
            / 12
        )   # principal+interest on lease portion, interest only on residual

        self.annual_repayment = D(self.monthly_repayment * 12)

        self.total_purchase_cost = D(
            self.annual_repayment * self.lease_term
            + self.residual_amount_inc_gst
        )

        self.name = '_'.join(
            [self.car.make, self.car.model, 'novated_lease']
        ).replace(' ', '_')


def main():
    st.set_page_config(page_title='Novated Lease Calculator', layout='wide')
    st.write('# Novated Lease Calculator')
    # getcontext().prec = 2

    interest_rate = D(
        st.sidebar.slider('Interest Rate', 1.0, 15.0, value=9.39, step=0.01)
        / 100,
        '0.0001',
    )

    lease_term = st.sidebar.selectbox('Lease Term', range(1, 6), index=3)
    lease_term = lease_term if lease_term is not None else 3

    outback = Car(
        make='Subaru',
        model='Outback',
        base_price_ex_gst=D(45000.0),
        accessories_price_ex_gst=D(2000.0),
        delivery_charges_ex_gst=D(1722.73),
        stamp_duty=D(1179.00),
    )

    model_y = Car(
        make='Tesla',
        model='Model Y',
        base_price_ex_gst=D(69800 * 0.9),
        accessories_price_ex_gst=D(500.0),
        delivery_charges_ex_gst=D(1800 * 0.9),
        stamp_duty=D(3966.0),
    )

    nvs = [
        NovatedLease(outback, interest_rate, lease_term),
        NovatedLease(model_y, interest_rate, lease_term),
    ]

    nvs_dict = [flatdict.FlatDict(asdict(nv)) for nv in nvs]

    # print(repr(nv))

    st.write(pd.DataFrame.from_records(nvs_dict, index='name').transpose())


if __name__ == '__main__':
    main()
