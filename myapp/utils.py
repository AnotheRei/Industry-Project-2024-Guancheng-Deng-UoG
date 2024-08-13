import matplotlib.pyplot as plt
from itertools import groupby
from operator import itemgetter
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
import pandas as pd
import base64
from io import BytesIO


def calculate_event_interval_in_months(start_date, end_date):
    interval = relativedelta(end_date, start_date)
    months = interval.years * 12 + interval.months + interval.days / 30.0
    return months

def parse_period_string(period_str):
    match = re.match(r'P(\d+)([MY])', period_str)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        return value, unit
    return None, None

class FinancialData:
    def __init__(self, IED, MD, PRCL, PRANX, Prnxt, FER, FEANX, FECL, SCRT, SCANX, SCCL, PYRT=None, MTCS=None):
        self.IED = IED
        self.MD = MD
        self.PRCL = PRCL
        self.PRANX = PRANX
        self.Prnxt = Prnxt
        self.FER = FER
        self.FEANX = FEANX
        self.FECL = FECL
        self.SCRT = SCRT
        self.SCANX = SCANX
        self.SCCL = SCCL
        self.PYRT = PYRT
        self.MTCS = MTCS or {}


def parse_user_input(data):
    IED = datetime.strptime(data['ied'], '%Y-%m-%dT%H:%M')
    MD = datetime.strptime(data['maturity'], '%Y-%m-%dT%H:%M')
    PRCL = data['cycle_of_rent_payment']
    PRANX = datetime.strptime(data['rent_pay_date'], '%Y-%m-%dT%H:%M') if data['rent_pay_date'] else None
    Prnxt = data['rent']
    FER = data.get('fee_rate', 0.0)
    FEANX = datetime.strptime(data.get('fee_payment_date'), '%Y-%m-%dT%H:%M') if data.get('fee_payment_date') else None
    FECL = data.get('cycle_of_fee_payment', '')
    SCRT = data.get('rent_scaling_rate', 0.0)
    SCANX = datetime.strptime(data.get('rent_scaling_date'), '%Y-%m-%dT%H:%M') if data.get('rent_scaling_date') else None
    SCCL = data.get('cycle_of_rent_scaling', '')
    PYRT = data.get('penalty_rate', 0.0)

    if FECL and not FEANX:
        fe_value, fe_unit = parse_period_string(FECL)
        if fe_value and fe_unit:
            FEANX = IED + relativedelta(months=fe_value) if fe_unit == 'M' else IED + relativedelta(years=fe_value)
    elif not FECL and FEANX:
        FECL = PRCL
    elif not FECL and not FEANX:
        FEANX = PRANX if PRANX else IED
        FECL = PRCL

    if SCRT == 0.0 or (not SCANX and not SCCL):
        SCRT = 0.0
        SCANX = None
        SCCL = None

    return FinancialData(IED, MD, PRCL, PRANX, Prnxt, FER, FEANX, FECL, SCRT, SCANX, SCCL, PYRT)

def generate_event_schedule(IED, MD, PRCL, PRANX, FEANX, FECL, SCANX, SCCL, SCRT):
    events = []

    events.append(('IED', IED))

    current_date = PRANX if PRANX else IED
    pr_value, pr_unit = parse_period_string(PRCL)
    if pr_value and pr_unit:
        while current_date < MD:
            events.append(('PR', current_date))
            if pr_unit == 'M':
                current_date += relativedelta(months=pr_value)
            elif pr_unit == 'Y':
                current_date += relativedelta(years=pr_value)

    if FECL:
        current_date = FEANX
        fe_value, fe_unit = parse_period_string(FECL)
        if fe_value and fe_unit:
            while current_date < MD:
                events.append(('FP', current_date))
                if fe_unit == 'M':
                    current_date += relativedelta(months=fe_value)
                elif fe_unit == 'Y':
                    current_date += relativedelta(years=fe_value)

    if SCRT != 0.0 and (SCANX or SCCL):
        if not SCANX and SCCL:
            sc_value, sc_unit = parse_period_string(SCCL)
            if sc_value and sc_unit:
                SCANX = IED + relativedelta(months=sc_value) if sc_unit == 'M' else IED + relativedelta(years=sc_value)
        current_date = SCANX
        if SCCL:
            sc_value, sc_unit = parse_period_string(SCCL)
            if sc_value and sc_unit:
                while current_date < MD:
                    events.append(('SC', current_date))
                    if sc_unit == 'M':
                        current_date += relativedelta(months=sc_value)
                    elif sc_unit == 'Y':
                        current_date += relativedelta(years=sc_value)
        else:
            events.append(('SC', current_date))  # Only one scaling event at SCANX if SCCL is not provided

    events.append(('MD', MD))

    events.sort(key=lambda x: x[1])

    return events

def calculate_cashflows(events, financial_data):
    Feac = 0.0
    Sd = financial_data.IED
    Rsc = 1.0
    rent_cashflows = []
    fee_cashflows = []
    previous_date = financial_data.IED

    event_types = ['IED', 'SC', 'PR', 'PY', 'MT', 'FP', 'MD']
    events.sort(key=itemgetter(1))
    grouped_events = groupby(events, key=itemgetter(1))

    for event_date, event_group in grouped_events:
        fee_accumulated_for_day = False
        day_events = list(event_group)
        day_events.sort(key=lambda x: event_types.index(x[0]))

        for event in day_events:
            event_type, event_date = event

            if event_type == 'IED':
                rent_cashflow = Rsc * financial_data.Prnxt
                rent_cashflows.append((financial_data.IED, rent_cashflow))
                fee_cashflows.append((financial_data.IED, 0))
                continue

            if financial_data.FER and not fee_accumulated_for_day:
                interval_months = calculate_event_interval_in_months(previous_date, event_date)
                Feac += interval_months * financial_data.Prnxt * financial_data.FER
                fee_accumulated_for_day = True

            if event_type == 'SC':
                if financial_data.SCRT:
                    Rsc = round(Rsc * (1 + financial_data.SCRT), 2)

            elif event_type == 'PR':
                rent_cashflow = Rsc * financial_data.Prnxt
                rent_cashflows.append((event_date, rent_cashflow))
                fee_cashflows.append((event_date, Feac))

            elif event_type == 'FP':
                fee_cashflows.append((event_date, Feac))
                rent_cashflows.append((event_date, rent_cashflows[-1][1]))
                fee_cashflows.append((event_date, 0))
                Feac = 0.0

            elif event_type == 'PY':
                fee_cashflows.append((event_date, Feac))
                penalty_amount = calculate_penalty_amount(financial_data.Prnxt, financial_data.PYRT)
                Feac += penalty_amount
                fee_cashflows.append((event_date, Feac))
                rent_cashflows.append((event_date, rent_cashflows[-1][1]))

            elif event_type == 'MT':
                fee_cashflows.append((event_date, Feac))
                Feac += financial_data.MTCS.get(event_date, 0)
                fee_cashflows.append((event_date, Feac))
                rent_cashflows.append((event_date, rent_cashflows[-1][1]))

            elif event_type == 'MD':
                rent_cashflows.append((event_date, Rsc * financial_data.Prnxt))
                fee_cashflows.append((event_date, Feac))
                Feac = 0.0

        previous_date = event_date
        Sd = event_date

    return rent_cashflows, fee_cashflows


def generate_event_table(events, financial_data):
    Feac = 0.0
    Sd = financial_data.IED
    Rsc = 1.0
    event_table = []
    previous_date = financial_data.IED

    event_table.append({
        'Event Date': financial_data.IED,
        'Event Type': 'IED',
        'Event Value': 0,
        'Event Currency': 'USD',
        'Fee Accrued': 0
    })

    event_types = ['IED', 'SC', 'PR', 'PY', 'MT', 'FP', 'MD']
    events.sort(key=itemgetter(1))
    grouped_events = groupby(events, key=itemgetter(1))

    for event_date, event_group in grouped_events:
        fee_accumulated_for_day = False
        day_events = list(event_group)
        day_events.sort(key=lambda x: event_types.index(x[0]))

        for event in day_events:
            event_type, event_date = event
            event_value = 0

            if financial_data.FER and not fee_accumulated_for_day:
                interval_months = calculate_event_interval_in_months(previous_date, event_date)
                Feac += interval_months * financial_data.Prnxt * financial_data.FER
                fee_accumulated_for_day = True

            fee_accrued = Feac

            if event_type == 'SC':
                if financial_data.SCRT:
                    Rsc = round(Rsc * (1 + financial_data.SCRT), 2)
                event_type = 'SC'

            elif event_type == 'PR':
                event_value = Rsc * financial_data.Prnxt
                event_type = 'PR'

            elif event_type == 'FP':
                event_value = Feac
                event_type = 'FP'
                Feac = 0.0

            elif event_type == 'PY':
                penalty_amount = calculate_penalty_amount(financial_data.Prnxt, financial_data.PYRT)
                Feac += penalty_amount
                event_value = 0
                fee_accrued = Feac

            elif event_type == 'MT':
                mt_cost = financial_data.MTCS.get(event_date, 0)
                Feac += mt_cost
                event_value = 0
                fee_accrued = Feac

            elif event_type == 'MD':
                event_value = Feac
                event_type = 'MD'
                Feac = 0.0

            event_table.append({
                'Event Date': event_date,
                'Event Type': event_type,
                'Event Value': event_value,
                'Event Currency': 'USD',
                'Fee Accrued': 0 if event_type == 'FP' or event_type == 'MD' else fee_accrued
            })

        previous_date = event_date
        Sd = event_date

    return pd.DataFrame(event_table)



def insert_new_events(events, new_events):
    for new_event in new_events:
        event_type, event_date = new_event

        if event_type == 'MT':
            if any(e for e in events if e[0] == 'MT' and e[1] == event_date):
                continue

        events.append((event_type, event_date))


    events.sort(key=lambda x: x[1])
    return events


def plot_cashflows(rent_cashflows, fee_cashflows):
    dates_rent = [cashflow[0] for cashflow in rent_cashflows]
    values_rent = [cashflow[1] for cashflow in rent_cashflows]
    dates_fee = [cashflow[0] for cashflow in fee_cashflows]
    values_fee = [cashflow[1] for cashflow in fee_cashflows]

    plt.figure(figsize=(25, 9))
    plt.step(dates_rent, values_rent, label='Rent Cashflow', where='post', linestyle='-', color='b', linewidth=2)
    plt.plot(dates_fee, values_fee, label='Fee Cashflow', linestyle='-', color='orange', linewidth=2)

    plt.xlabel('Date', fontsize=10)
    plt.ylabel('Cashflow', fontsize=10)
    plt.title('Cashflow over Time', fontsize=14)
    plt.legend()

    plt.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray', alpha=0.7)

    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()

    return image_base64

def calculate_penalty_amount(Prnxt, PYRT):
    return Prnxt * PYRT


def process_update_event(data, form, events, financial_data):
    new_events = []


    late_payment_date_str = data.get('late_payment_date')
    if late_payment_date_str:
        try:
            late_payment_date = datetime.strptime(late_payment_date_str, '%Y-%m-%dT%H:%M')
            new_events.append(('PY', late_payment_date))
        except ValueError:
            late_payment_date = None

    maintenance_date_str = data.get('maintenance_date')
    maintenance_cost = data.get('maintenance_cost')
    if maintenance_date_str and maintenance_cost:
        try:
            maintenance_date = datetime.strptime(maintenance_date_str, '%Y-%m-%dT%H:%M')
            maintenance_cost = float(maintenance_cost)
            new_events.append(('MT', maintenance_date))
            if maintenance_date in financial_data.MTCS:
                financial_data.MTCS[maintenance_date] += maintenance_cost
            else:
                financial_data.MTCS[maintenance_date] = maintenance_cost
        except ValueError:
            maintenance_date = None
            maintenance_cost = None

    if new_events:
        events = insert_new_events(events, new_events)
        rent_cashflows, fee_cashflows = calculate_cashflows(events, financial_data)
        chart = plot_cashflows(rent_cashflows, fee_cashflows)
        event_table = generate_event_table(events, financial_data)
        event_table_html = event_table.to_html(index=False)

        print("Updated MTCS after insert: ", financial_data.MTCS)

        return chart, event_table_html

    return None, None

