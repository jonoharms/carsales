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

TAX_RATE = D(0.325, '0.001')
MEDICARE_RATE = D(0.02, '0.01')


def spaced_line(name: str, number: Decimal):
    spaces = 40 - len(name)
    return '**' + name + ':**' + '&nbsp;' * spaces + f'{number:,.2f}'


@define
class Car:
    make: str
    model: str
    base_price_ex_gst: Decimal
    accessories_price_ex_gst: Decimal
    delivery_charges_ex_gst: Decimal
    is_electric: bool
    annual_running_costs: Decimal

    stamp_duty: Decimal = field(init=False)

    total_price_inc_gst: Decimal = field(init=False)
    total_price_inc_gst_and_sd: Decimal = field(init=False)
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
        self.stamp_duty = D(self.total_price_inc_gst * D(8.4) / D(200))
        self.total_price_inc_gst_and_sd = D(
            self.total_price_inc_gst + self.stamp_duty
        )


@define
class NovatedLease:
    car: Car
    interest_rate: Decimal
    lease_term: int
    name: str = field(init=False)
    financed_amount: Decimal = field(init=False)
    residual_amount_ex_gst: Decimal = field(init=False)
    residual_amount_inc_gst: Decimal = field(init=False)
    monthly_lease: Decimal = field(init=False)
    annual_lease: Decimal = field(init=False)
    total_purchase_cost: Decimal = field(init=False)
    fbt: Decimal = field(init=False)
    fbt_taxable_value: Decimal = field(init=False)
    annual_repayment_before_tax: Decimal = field(init=False)
    annual_repayment_post_tax: Decimal = field(init=False)
    annual_tax_saving: Decimal = field(init=False)
    annual_repayment_full: Decimal = field(init=False)

    def __attrs_post_init__(self):
        self.fbt_taxable_value = D(self.car.total_price_inc_gst * D(0.2))
        self.fbt = D(self.fbt_taxable_value * D(2.0802 * 0.47, '0.0001'))

        self.financed_amount = (
            self.car.total_price_ex_gst + self.car.stamp_duty
        )
        self.residual_amount_ex_gst = D(
            self.financed_amount * RESIDUAL[self.lease_term] / 100
        )
        self.residual_amount_inc_gst = D(
            D(self.residual_amount_ex_gst) * D(1.1)
        )
        self.monthly_lease = D(
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

        self.annual_lease = D(self.monthly_lease * 12)

        self.annual_repayment_before_tax = (
            self.annual_lease
            if self.car.is_electric
            else self.annual_lease - self.fbt_taxable_value
        )

        self.annual_repayment_post_tax = (
            D(0.0) if self.car.is_electric else self.fbt_taxable_value
        )

        self.annual_tax_saving = D(
            self.annual_repayment_before_tax * (TAX_RATE + MEDICARE_RATE)
        )

        self.annual_repayment_full = (
            self.annual_repayment_before_tax
            + self.annual_repayment_post_tax
            - self.annual_tax_saving
        )

        self.total_purchase_cost = D(
            self.annual_repayment_full * self.lease_term
            + self.residual_amount_inc_gst
        )

        self.name = '_'.join(
            [self.car.make, self.car.model, 'novated_lease']
        ).replace(' ', '_')


def main():
    st.set_page_config(page_title='Novated Lease Calculator', layout='wide')
    st.write('# Novated Lease Calculator')

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
        base_price_ex_gst=D(42690.0 / 1.1),
        accessories_price_ex_gst=D(0.0),
        delivery_charges_ex_gst=D(2246),
        is_electric=False,
        annual_running_costs=D(860),
    )

    model_y = Car(
        make='Tesla',
        model='Model Y',
        base_price_ex_gst=D(68900 / 1.1),
        accessories_price_ex_gst=D(0.0),
        delivery_charges_ex_gst=D(1800 / 1.1),
        is_electric=True,
        annual_running_costs=D(860),
    )

    nvs = [
        NovatedLease(outback, interest_rate, lease_term),
        NovatedLease(model_y, interest_rate, lease_term),
    ]

    nvs_dict = [flatdict.FlatDict(asdict(nv)) for nv in nvs]
    st.write(pd.DataFrame.from_records(nvs_dict, index='name').transpose())


if __name__ == '__main__':
    main()
