from django.db import models

class FinancialData(models.Model):
    contract_type = models.CharField(max_length=20, default='Lease')
    contract_identifier = models.CharField(max_length=100, default='')
    ied = models.CharField(max_length=20)
    maturity = models.CharField(max_length=20)
    cycle_of_rent_payment = models.CharField(max_length=10)
    rent_pay_date = models.CharField(max_length=20, blank=True, null=True)
    rent = models.FloatField()
    fee_rate = models.FloatField(blank=True, null=True)
    fee_payment_date = models.CharField(max_length=20, blank=True, null=True)
    cycle_of_fee_payment = models.CharField(max_length=10, blank=True, null=True)
    rent_scaling_rate = models.FloatField(blank=True, null=True)
    rent_scaling_date = models.CharField(max_length=20, blank=True, null=True)
    cycle_of_rent_scaling = models.CharField(max_length=10, blank=True, null=True)
    penalty_rate = models.FloatField(blank=True, null=True)
    late_payment_date = models.CharField(max_length=20, blank=True, null=True) 
    maintenance_date = models.CharField(max_length=20, blank=True, null=True)
    maintenance_cost = models.FloatField(blank=True, null=True) 

    def __str__(self):
        return self.ied
