from django import forms
from .models import FinancialData
import re

DATE_FORMAT_REGEX = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$'
PERIOD_FORMAT_REGEX = r'^P\d+[MY]$'

class FinancialDataForm(forms.ModelForm):
    class Meta:
        model = FinancialData
        fields = '__all__'
        widgets = {
            'contract_type': forms.Select(choices=[('Lease', 'Lease')], attrs={'class': 'form-control'}),
            'ied': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DDTHH:MM', 'class': 'form-control'}),
            'maturity': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DDTHH:MM', 'class': 'form-control'}),
            'rent_pay_date': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DDTHH:MM', 'class': 'form-control'}),
            'fee_payment_date': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DDTHH:MM', 'class': 'form-control'}),
            'rent_scaling_date': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DDTHH:MM', 'class': 'form-control'}),
            'late_payment_date': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DDTHH:MM', 'class': 'form-control'}),
            'maintenance_date': forms.TextInput(attrs={'placeholder': 'YYYY-MM-DDTHH:MM', 'class': 'form-control'}),
            'maintenance_cost': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        maintenance_date = cleaned_data.get('maintenance_date')
        maintenance_cost = cleaned_data.get('maintenance_cost')

        # Validate date fields
        date_fields = ['ied', 'maturity', 'rent_pay_date', 'fee_payment_date',
                       'rent_scaling_date', 'late_payment_date', 'maintenance_date']
        for field in date_fields:
            date_value = cleaned_data.get(field)
            if date_value and not re.match(DATE_FORMAT_REGEX, date_value):
                self.add_error(field, 'Enter a valid date in YYYY-MM-DDTHH:MM format.')

        # Validate period fields
        period_fields = ['cycle_of_rent_payment', 'cycle_of_fee_payment', 'cycle_of_rent_scaling']
        for field in period_fields:
            period_value = cleaned_data.get(field)
            if period_value and not re.match(PERIOD_FORMAT_REGEX, period_value):
                self.add_error(field, 'Enter a valid period format (e.g., P1M, P3Y).')

        # Maintenance date and cost validation
        if (maintenance_date and not maintenance_cost) or (maintenance_cost and not maintenance_date):
            raise forms.ValidationError('Both maintenance date and cost must be provided together.')

        return cleaned_data
