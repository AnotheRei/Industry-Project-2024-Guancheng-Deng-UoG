from django.shortcuts import render, redirect
from .forms import FinancialDataForm
from .utils import parse_user_input, generate_event_schedule, calculate_cashflows, plot_cashflows, generate_event_table, insert_new_events, process_update_event
from datetime import datetime

def clear_session_data(request, keys):
    for key in keys:
        if key in request.session:
            del request.session[key]

def store_session_data(request, events, financial_data, chart, event_table_html):
    request.session['events'] = [(etype, edate.strftime('%Y-%m-%dT%H:%M')) for etype, edate in events]
    request.session['mtcs'] = {k.strftime('%Y-%m-%dT%H:%M'): v for k, v in financial_data.MTCS.items()}
    request.session['chart'] = chart
    request.session['event_table'] = event_table_html

def index(request):
    errors = None
    if request.method == 'POST':
        if 'reset' in request.POST:
            clear_session_data(request, ['form_data', 'events', 'mtcs', 'chart', 'event_table'])
            return redirect('index')

        form = FinancialDataForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            request.session['form_data'] = request.POST
            financial_data = parse_user_input(data)
            
            if 'events' in request.session:
                events = request.session['events']
                events = [(etype, datetime.strptime(edate, '%Y-%m-%dT%H:%M')) for etype, edate in events]
                if 'mtcs' in request.session:
                    financial_data.MTCS = {datetime.strptime(k, '%Y-%m-%dT%H:%M'): v for k, v in request.session['mtcs'].items()}
            else:
                events = generate_event_schedule(
                    financial_data.IED, financial_data.MD, financial_data.PRCL, 
                    financial_data.PRANX, financial_data.FEANX, financial_data.FECL, 
                    financial_data.SCANX, financial_data.SCCL, financial_data.SCRT
                )
            
            if 'update' in request.POST:
                chart, event_table_html = process_update_event(data, form, events, financial_data)
                if chart and event_table_html:
                    store_session_data(request, events, financial_data, chart, event_table_html)
                    contract_id = data['contract_identifier']
                    show_late_payment_date = 'penalty_rate' in data and data['penalty_rate'] is not None
                    errors = form.errors.get('__all__', None)
                    empty_form = FinancialDataForm()                    
                    return render(request, 'chart.html', {
                        'form': form, 
                        'chart': chart, 
                        'event_table': event_table_html, 
                        'contract_id': contract_id, 
                        'show_late_payment_date': show_late_payment_date,
                        'errors': errors
                    })

            rent_cashflows, fee_cashflows = calculate_cashflows(events, financial_data)
            chart = plot_cashflows(rent_cashflows, fee_cashflows)
            event_table = generate_event_table(events, financial_data)
            event_table_html = event_table.to_html(index=False)
            contract_id = data['contract_identifier']
            show_late_payment_date = 'penalty_rate' in data and data['penalty_rate'] is not None

            store_session_data(request, events, financial_data, chart, event_table_html)
            errors = form.errors.get('__all__', None)
            
            return render(request, 'chart.html', {
                'form': form, 
                'chart': chart, 
                'event_table': event_table_html, 
                'contract_id': contract_id, 
                'show_late_payment_date': show_late_payment_date,
                'errors': errors
            })
        else:
            form_source = request.POST.get('form_source')
            errors = form.non_field_errors()  
            if form_source == 'chart':
                contract_id = request.POST.get('contract_identifier')
                show_late_payment_date = 'penalty_rate' in request.POST and request.POST['penalty_rate']
                chart = request.session.get('chart')
                event_table = request.session.get('event_table')
                return render(request, 'chart.html', {
                    'form': form,
                    'chart': chart,
                    'event_table': event_table,
                    'contract_id': contract_id,
                    'show_late_payment_date': show_late_payment_date,
                    'errors': errors
                })
            else:
                return render(request, 'index.html', {'form': form, 'errors': form.errors})

    else:
        clear_session_data(request, ['events', 'mtcs'])
        if 'returning' not in request.GET and 'form_data' in request.session:
            del request.session['form_data']
                
        form_data = request.session.get('form_data')
        if form_data:
            form = FinancialDataForm(initial=form_data)
        else:
            form = FinancialDataForm()
    return render(request, 'index.html', {'form': form})
