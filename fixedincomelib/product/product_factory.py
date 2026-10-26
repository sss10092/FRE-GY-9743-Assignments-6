"""Convention-driven factory adapted from the instructor template.

Swap axis1 is tenor or start-offset x tenor. FRA uses start-offset x end-offset,
with both offsets measured from value_date, or two explicit ISO dates.
"""

from typing import Any
from fixedincomelib.date import Date, TermOrDate, add_period
from fixedincomelib.market.data_conventions import (
    CompoundingMethod, DataConvention, DataConventionFRA,
    DataConventionRFRSwap, DataConventionOvernightIndexBasisSwap,
)
from fixedincomelib.product.product_interfaces import ProductBuilderRegistry
from fixedincomelib.product.linear_products import ProductFRA, ProductRFRSwap, ProductOvernightIndexBasisSwap
from fixedincomelib.product.utilities import PayOrReceive


class ProductFactory:
    @classmethod
    def create_product_from_data_convention(
        cls,
        value_date: Date,
        axis1: str,
        data_convention: DataConvention,
        values: float,
        **kwargs: Any,
    ):

        convention_obj: DataConvention = data_convention
        prod_type = convention_obj.type()
        func = ProductBuilderRegistry().get(prod_type)
        return func(value_date, axis1, convention_obj, values, **kwargs)

    @classmethod
    def create_rfr_swap(
        cls,
        value_date: Date,
        axis1: str,
        data_convention: DataConventionRFRSwap,
        values: float,
        **kwargs: Any,
    ) -> ProductRFRSwap:

        first, second = cls._tokenize_axis1(axis1)
        bdc = data_convention.business_day_convention
        holidays = data_convention.holiday_convention
        if second is None:                      #"1Y": spot-starting
            effective_date, term = value_date, first
        elif first.is_term():                   #"3Mx1Y": start offset x tenor
            effective_date = add_period(value_date, first.get_term(), bdc, holidays)
            term = second
        else:                                   #"dateXdate"
            effective_date, term = first.get_date(), second
        return ProductRFRSwap(
            effective_date, term, data_convention.payment_offset, data_convention.index_str,
            values, PayOrReceive.from_string(kwargs.get("pay_or_rec", "receive")),
            kwargs.get("notional", 1e4), data_convention.acc_period, data_convention.acc_basis,
            data_convention.acc_period, bdc, holidays, 0.0, data_convention.compounding_method,
        )
        pass

    @classmethod
    def create_overnight_index_basis_swap(
        cls,
        value_date: Date,
        axis1: str,
        data_convention: DataConventionOvernightIndexBasisSwap,
        values: float,
        **kwargs: Any,
    ) -> ProductOvernightIndexBasisSwap:

        first, second = cls._tokenize_axis1(axis1)
        bdc = data_convention.business_day_convention
        holidays = data_convention.holiday_convention
        if second is None:
            effective_date, term = value_date, first
        elif first.is_term():
            effective_date = add_period(value_date, first.get_term(), bdc, holidays)
            term = second
        else:
            effective_date, term = first.get_date(), second
        return ProductOvernightIndexBasisSwap(
            effective_date, term, data_convention.payment_offset,
            data_convention.index_1_str, data_convention.index_2_str, values,
            PayOrReceive.from_string(kwargs.get("pay_or_rec", "receive")),
            kwargs.get("notional", 1e4), data_convention.acc_period_1, data_convention.acc_basis,
            data_convention.acc_period_2, bdc, holidays, data_convention.compounding_method,
        )
        pass

    @classmethod
    def create_fra(cls, value_date, axis1, data_convention, values, **kwargs):
        start, end = cls._tokenize_axis1(axis1)
        bdc = data_convention.business_day_convention
        holidays = data_convention.holiday_convention
        if start.is_term():
            effective_date = add_period(value_date, start.get_term(), bdc, holidays)
            termination_date = add_period(value_date, end.get_term(), bdc, holidays)
        else:
            effective_date = start.get_date()
            termination_date = end.get_date()
        return ProductFRA(
            effective_date, TermOrDate(termination_date), data_convention.index_str,
            values, PayOrReceive.from_string(kwargs.get("pay_or_rec", "receive")),
            kwargs.get("notional", 1e4), data_convention.acc_basis, bdc, holidays,
        )

    @staticmethod
    def _tokenize_axis1(axis1):
        tokens = axis1.strip().replace("X", "x").split("x")
        first = TermOrDate(tokens[0].strip())
        second = TermOrDate(tokens[1].strip()) if len(tokens) == 2 else None
        return first, second


ProductBuilderRegistry().register(DataConventionFRA.type(), ProductFactory.create_fra)
ProductBuilderRegistry().register(DataConventionRFRSwap.type(), ProductFactory.create_rfr_swap)
ProductBuilderRegistry().register(DataConventionOvernightIndexBasisSwap.type(),
                                  ProductFactory.create_overnight_index_basis_swap)
