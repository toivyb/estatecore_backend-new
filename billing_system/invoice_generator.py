import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import base64
from io import BytesIO

class InvoiceTemplate(Enum):
    STANDARD = "standard"
    DETAILED = "detailed"
    SUMMARY = "summary"
    CUSTOM = "custom"

class TaxCalculationType(Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    EXEMPT = "exempt"

@dataclass
class InvoiceLineItem:
    line_id: str
    description: str
    quantity: float
    unit_price: float
    total_price: float
    metric_name: str
    period_start: datetime
    period_end: datetime
    is_overage: bool
    metadata: Dict[str, Any]

@dataclass
class TaxItem:
    tax_id: str
    name: str
    rate: float
    amount: float
    calculation_type: TaxCalculationType
    jurisdiction: str

@dataclass
class PaymentTerm:
    term_id: str
    name: str
    days: int
    description: str
    discount_percentage: float
    discount_days: int

@dataclass
class InvoiceSettings:
    company_name: str
    company_address: Dict[str, str]
    company_logo_url: str
    tax_id: str
    payment_terms: PaymentTerm
    currency: str
    timezone: str
    late_fee_percentage: float
    late_fee_grace_days: int
    auto_send: bool
    send_reminders: bool
    reminder_schedule: List[int]  # Days before due date

class InvoiceGenerator:
    """
    Advanced invoice generation system with templates and customization
    """
    
    def __init__(self):
        self.templates = {}
        self.invoice_settings = None
        self.tax_rates = {}
        self.payment_terms = {}
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Initialize default settings and templates"""
        
        # Default payment terms
        self.payment_terms['net_30'] = PaymentTerm(
            term_id="net_30",
            name="Net 30",
            days=30,
            description="Payment due within 30 days",
            discount_percentage=0.0,
            discount_days=0
        )
        
        self.payment_terms['net_15'] = PaymentTerm(
            term_id="net_15",
            name="Net 15",
            days=15,
            description="Payment due within 15 days",
            discount_percentage=0.0,
            discount_days=0
        )
        
        self.payment_terms['2_10_net_30'] = PaymentTerm(
            term_id="2_10_net_30",
            name="2/10 Net 30",
            days=30,
            description="2% discount if paid within 10 days, otherwise due in 30 days",
            discount_percentage=2.0,
            discount_days=10
        )
        
        # Default invoice settings
        self.invoice_settings = InvoiceSettings(
            company_name="EstateCore SaaS",
            company_address={
                "street": "123 Tech Plaza",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94105",
                "country": "USA"
            },
            company_logo_url="https://estatecore.com/logo.png",
            tax_id="12-3456789",
            payment_terms=self.payment_terms['net_30'],
            currency="USD",
            timezone="America/Los_Angeles",
            late_fee_percentage=1.5,
            late_fee_grace_days=5,
            auto_send=True,
            send_reminders=True,
            reminder_schedule=[7, 3, 1]  # 7 days, 3 days, 1 day before due
        )
        
        # Default tax rates by jurisdiction
        self.tax_rates['US_CA'] = TaxItem(
            tax_id="us_ca_sales",
            name="California Sales Tax",
            rate=8.75,
            amount=0.0,
            calculation_type=TaxCalculationType.PERCENTAGE,
            jurisdiction="California, USA"
        )
        
        self.tax_rates['US_NY'] = TaxItem(
            tax_id="us_ny_sales",
            name="New York Sales Tax",
            rate=8.25,
            amount=0.0,
            calculation_type=TaxCalculationType.PERCENTAGE,
            jurisdiction="New York, USA"
        )
        
        self.tax_rates['EU_VAT'] = TaxItem(
            tax_id="eu_vat",
            name="European VAT",
            rate=20.0,
            amount=0.0,
            calculation_type=TaxCalculationType.PERCENTAGE,
            jurisdiction="European Union"
        )
    
    def generate_line_items(self, usage_summary: Dict[str, Any], 
                           subscription_limits: Dict[str, Any]) -> List[InvoiceLineItem]:
        """Generate line items from usage summary"""
        
        line_items = []
        
        # Base subscription line item
        base_item = InvoiceLineItem(
            line_id=str(uuid.uuid4()),
            description=f"EstateCore {subscription_limits.get('tier', 'Professional')} Plan",
            quantity=1.0,
            unit_price=subscription_limits.get('base_price', 299.0),
            total_price=subscription_limits.get('base_price', 299.0),
            metric_name="base_subscription",
            period_start=datetime.fromisoformat(usage_summary['period_start']),
            period_end=datetime.fromisoformat(usage_summary['period_end']),
            is_overage=False,
            metadata={
                'tier': subscription_limits.get('tier'),
                'billing_cycle': subscription_limits.get('billing_cycle', 'monthly')
            }
        )
        line_items.append(base_item)
        
        # Usage-based line items
        for metric_name, metric_data in usage_summary.get('metrics', {}).items():
            if not metric_data.get('billable', False):
                continue
            
            # Check if this is an overage
            included_amount = subscription_limits.get(f"{metric_name}_included", 0)
            total_usage = metric_data['total_value']
            
            if total_usage > included_amount:
                # Overage charge
                overage_amount = total_usage - included_amount
                overage_price = overage_amount * metric_data['price_per_unit']
                
                overage_item = InvoiceLineItem(
                    line_id=str(uuid.uuid4()),
                    description=f"{metric_data['name']} Overage ({overage_amount:.2f} {metric_data['unit']})",
                    quantity=overage_amount,
                    unit_price=metric_data['price_per_unit'],
                    total_price=overage_price,
                    metric_name=metric_name,
                    period_start=datetime.fromisoformat(usage_summary['period_start']),
                    period_end=datetime.fromisoformat(usage_summary['period_end']),
                    is_overage=True,
                    metadata={
                        'included_amount': included_amount,
                        'total_usage': total_usage,
                        'overage_amount': overage_amount
                    }
                )
                line_items.append(overage_item)
        
        return line_items
    
    def calculate_taxes(self, line_items: List[InvoiceLineItem], 
                       customer_jurisdiction: str) -> List[TaxItem]:
        """Calculate taxes for line items"""
        
        taxes = []
        
        # Get applicable tax rate
        tax_template = self.tax_rates.get(customer_jurisdiction)
        if not tax_template:
            # Default to no tax for unknown jurisdictions
            return taxes
        
        # Calculate taxable amount
        taxable_amount = sum(item.total_price for item in line_items)
        
        if tax_template.calculation_type == TaxCalculationType.PERCENTAGE:
            tax_amount = taxable_amount * (tax_template.rate / 100)
        elif tax_template.calculation_type == TaxCalculationType.FIXED:
            tax_amount = tax_template.rate
        else:  # EXEMPT
            tax_amount = 0.0
        
        if tax_amount > 0:
            tax = TaxItem(
                tax_id=tax_template.tax_id,
                name=tax_template.name,
                rate=tax_template.rate,
                amount=tax_amount,
                calculation_type=tax_template.calculation_type,
                jurisdiction=tax_template.jurisdiction
            )
            taxes.append(tax)
        
        return taxes
    
    def generate_invoice_data(self, subscription: Dict[str, Any], usage_summary: Dict[str, Any],
                            customer_info: Dict[str, Any], template: InvoiceTemplate = InvoiceTemplate.STANDARD) -> Dict[str, Any]:
        """Generate complete invoice data structure"""
        
        invoice_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Generate invoice number
        invoice_number = f"INV-{now.strftime('%Y%m')}-{int(time.time()) % 10000:04d}"
        
        # Generate line items
        line_items = self.generate_line_items(usage_summary, subscription)
        
        # Calculate taxes
        customer_jurisdiction = customer_info.get('tax_jurisdiction', 'US_CA')
        taxes = self.calculate_taxes(line_items, customer_jurisdiction)
        
        # Calculate totals
        subtotal = sum(item.total_price for item in line_items)
        tax_total = sum(tax.amount for tax in taxes)
        
        # Apply discounts if eligible
        discount_amount = 0.0
        payment_terms = self.invoice_settings.payment_terms
        if payment_terms.discount_percentage > 0:
            # Early payment discount is potential, not automatically applied
            potential_discount = subtotal * (payment_terms.discount_percentage / 100)
        else:
            potential_discount = 0.0
        
        total_amount = subtotal + tax_total - discount_amount
        
        # Due date
        due_date = now + timedelta(days=payment_terms.days)
        
        invoice_data = {
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'template': template.value,
            
            # Dates
            'issue_date': now.isoformat(),
            'due_date': due_date.isoformat(),
            'period_start': usage_summary['period_start'],
            'period_end': usage_summary['period_end'],
            
            # Company info
            'company': {
                'name': self.invoice_settings.company_name,
                'address': self.invoice_settings.company_address,
                'logo_url': self.invoice_settings.company_logo_url,
                'tax_id': self.invoice_settings.tax_id
            },
            
            # Customer info
            'customer': {
                'id': customer_info.get('customer_id'),
                'company_name': customer_info.get('company_name'),
                'contact_name': customer_info.get('contact_name'),
                'email': customer_info.get('email'),
                'address': customer_info.get('address', {}),
                'tax_jurisdiction': customer_jurisdiction
            },
            
            # Subscription info
            'subscription': {
                'id': subscription.get('subscription_id'),
                'tier': subscription.get('tier'),
                'billing_cycle': subscription.get('billing_cycle'),
                'status': subscription.get('status')
            },
            
            # Line items
            'line_items': [self._serialize_line_item(item) for item in line_items],
            
            # Taxes
            'taxes': [self._serialize_tax_item(tax) for tax in taxes],
            
            # Amounts
            'amounts': {
                'subtotal': round(subtotal, 2),
                'tax_total': round(tax_total, 2),
                'discount_amount': round(discount_amount, 2),
                'total_amount': round(total_amount, 2),
                'currency': self.invoice_settings.currency,
                'potential_early_discount': round(potential_discount, 2)
            },
            
            # Payment terms
            'payment_terms': {
                'name': payment_terms.name,
                'days': payment_terms.days,
                'description': payment_terms.description,
                'discount_percentage': payment_terms.discount_percentage,
                'discount_days': payment_terms.discount_days
            },
            
            # Usage summary
            'usage_summary': usage_summary,
            
            # Status
            'status': 'pending',
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }
        
        return invoice_data
    
    def _serialize_line_item(self, item: InvoiceLineItem) -> Dict[str, Any]:
        """Serialize line item to dict"""
        return {
            'line_id': item.line_id,
            'description': item.description,
            'quantity': item.quantity,
            'unit_price': round(item.unit_price, 2),
            'total_price': round(item.total_price, 2),
            'metric_name': item.metric_name,
            'period_start': item.period_start.isoformat(),
            'period_end': item.period_end.isoformat(),
            'is_overage': item.is_overage,
            'metadata': item.metadata
        }
    
    def _serialize_tax_item(self, tax: TaxItem) -> Dict[str, Any]:
        """Serialize tax item to dict"""
        return {
            'tax_id': tax.tax_id,
            'name': tax.name,
            'rate': tax.rate,
            'amount': round(tax.amount, 2),
            'calculation_type': tax.calculation_type.value,
            'jurisdiction': tax.jurisdiction
        }
    
    def generate_html_invoice(self, invoice_data: Dict[str, Any]) -> str:
        """Generate HTML invoice"""
        
        template = invoice_data.get('template', 'standard')
        
        if template == 'detailed':
            return self._generate_detailed_html(invoice_data)
        elif template == 'summary':
            return self._generate_summary_html(invoice_data)
        else:
            return self._generate_standard_html(invoice_data)
    
    def _generate_standard_html(self, invoice_data: Dict[str, Any]) -> str:
        """Generate standard HTML invoice template"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Invoice {invoice_data['invoice_number']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
                .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; border-bottom: 2px solid #2563eb; padding-bottom: 20px; }}
                .company-info {{ flex: 1; }}
                .company-logo {{ max-height: 60px; }}
                .invoice-title {{ font-size: 32px; font-weight: bold; color: #2563eb; }}
                .invoice-details {{ margin-bottom: 40px; }}
                .billing-info {{ display: flex; justify-content: space-between; margin-bottom: 40px; }}
                .billing-section {{ flex: 1; margin-right: 20px; }}
                .billing-section h3 {{ color: #2563eb; border-bottom: 1px solid #e5e7eb; padding-bottom: 5px; }}
                .line-items {{ margin-bottom: 40px; }}
                .line-items table {{ width: 100%; border-collapse: collapse; }}
                .line-items th, .line-items td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
                .line-items th {{ background-color: #f8fafc; font-weight: bold; color: #374151; }}
                .line-items .amount {{ text-align: right; }}
                .totals {{ margin-top: 20px; text-align: right; }}
                .totals table {{ margin-left: auto; }}
                .totals th, .totals td {{ padding: 8px 20px; }}
                .total-row {{ font-weight: bold; font-size: 18px; border-top: 2px solid #2563eb; }}
                .payment-terms {{ background-color: #f8fafc; padding: 20px; border-radius: 8px; margin-top: 40px; }}
                .footer {{ margin-top: 40px; text-align: center; color: #6b7280; font-size: 14px; }}
                .overage {{ color: #dc2626; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="company-info">
                    <h1>{invoice_data['company']['name']}</h1>
                    <p>{invoice_data['company']['address']['street']}<br>
                    {invoice_data['company']['address']['city']}, {invoice_data['company']['address']['state']} {invoice_data['company']['address']['zip_code']}<br>
                    {invoice_data['company']['address']['country']}</p>
                    <p>Tax ID: {invoice_data['company']['tax_id']}</p>
                </div>
                <div class="invoice-title">INVOICE</div>
            </div>
            
            <div class="invoice-details">
                <h2>Invoice #{invoice_data['invoice_number']}</h2>
                <p><strong>Issue Date:</strong> {datetime.fromisoformat(invoice_data['issue_date']).strftime('%B %d, %Y')}</p>
                <p><strong>Due Date:</strong> {datetime.fromisoformat(invoice_data['due_date']).strftime('%B %d, %Y')}</p>
                <p><strong>Billing Period:</strong> {datetime.fromisoformat(invoice_data['period_start']).strftime('%B %d, %Y')} - {datetime.fromisoformat(invoice_data['period_end']).strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="billing-info">
                <div class="billing-section">
                    <h3>Bill To:</h3>
                    <p><strong>{invoice_data['customer']['company_name']}</strong><br>
                    {invoice_data['customer'].get('contact_name', '')}<br>
                    {invoice_data['customer'].get('address', {}).get('street', '')}<br>
                    {invoice_data['customer'].get('address', {}).get('city', '')}, {invoice_data['customer'].get('address', {}).get('state', '')} {invoice_data['customer'].get('address', {}).get('zip_code', '')}<br>
                    {invoice_data['customer'].get('email', '')}</p>
                </div>
                
                <div class="billing-section">
                    <h3>Subscription Details:</h3>
                    <p><strong>Plan:</strong> {invoice_data['subscription']['tier'].title()}<br>
                    <strong>Billing Cycle:</strong> {invoice_data['subscription']['billing_cycle'].title()}<br>
                    <strong>Subscription ID:</strong> {invoice_data['subscription']['id']}</p>
                </div>
            </div>
            
            <div class="line-items">
                <table>
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Period</th>
                            <th>Quantity</th>
                            <th>Unit Price</th>
                            <th class="amount">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add line items
        for item in invoice_data['line_items']:
            period_str = f"{datetime.fromisoformat(item['period_start']).strftime('%m/%d')} - {datetime.fromisoformat(item['period_end']).strftime('%m/%d/%Y')}"
            overage_class = 'overage' if item['is_overage'] else ''
            
            html += f"""
                        <tr class="{overage_class}">
                            <td>{item['description']}</td>
                            <td>{period_str}</td>
                            <td>{item['quantity']:,.2f} {item.get('unit', '')}</td>
                            <td>${item['unit_price']:,.2f}</td>
                            <td class="amount">${item['total_price']:,.2f}</td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
            
            <div class="totals">
                <table>
        """
        
        # Add totals
        amounts = invoice_data['amounts']
        html += f"""
                    <tr>
                        <th>Subtotal:</th>
                        <td>${amounts['subtotal']:,.2f}</td>
                    </tr>
        """
        
        # Add taxes
        for tax in invoice_data['taxes']:
            html += f"""
                    <tr>
                        <th>{tax['name']} ({tax['rate']}%):</th>
                        <td>${tax['amount']:,.2f}</td>
                    </tr>
            """
        
        if amounts['discount_amount'] > 0:
            html += f"""
                    <tr>
                        <th>Discount:</th>
                        <td>-${amounts['discount_amount']:,.2f}</td>
                    </tr>
            """
        
        html += f"""
                    <tr class="total-row">
                        <th>Total Amount:</th>
                        <td>${amounts['total_amount']:,.2f} {amounts['currency']}</td>
                    </tr>
                </table>
            </div>
            
            <div class="payment-terms">
                <h3>Payment Terms</h3>
                <p>{invoice_data['payment_terms']['description']}</p>
        """
        
        if amounts['potential_early_discount'] > 0:
            html += f"""
                <p><strong>Early Payment Discount:</strong> Pay within {invoice_data['payment_terms']['discount_days']} days and save ${amounts['potential_early_discount']:,.2f} ({invoice_data['payment_terms']['discount_percentage']}% discount)</p>
            """
        
        html += """
            </div>
            
            <div class="footer">
                <p>Thank you for your business!</p>
                <p>Questions about this invoice? Contact us at billing@estatecore.com</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_detailed_html(self, invoice_data: Dict[str, Any]) -> str:
        """Generate detailed HTML invoice with usage breakdown"""
        
        # Start with standard template
        html = self._generate_standard_html(invoice_data)
        
        # Add detailed usage section before totals
        usage_section = """
            <div class="usage-breakdown">
                <h3>Usage Details</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Included</th>
                            <th>Used</th>
                            <th>Overage</th>
                            <th>Rate</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for metric_name, metric_data in invoice_data['usage_summary'].get('metrics', {}).items():
            if metric_data.get('billable', False):
                usage_section += f"""
                        <tr>
                            <td>{metric_data['name']}</td>
                            <td>-</td>
                            <td>{metric_data['total_value']:,.2f} {metric_data['unit']}</td>
                            <td>-</td>
                            <td>${metric_data['price_per_unit']:,.4f}</td>
                        </tr>
                """
        
        usage_section += """
                    </tbody>
                </table>
            </div>
        """
        
        # Insert usage section before totals
        html = html.replace('<div class="totals">', usage_section + '<div class="totals">')
        
        return html
    
    def _generate_summary_html(self, invoice_data: Dict[str, Any]) -> str:
        """Generate summary HTML invoice"""
        
        # Simplified version with just key information
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Invoice {invoice_data['invoice_number']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .summary {{ max-width: 600px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .amount {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
            </style>
        </head>
        <body>
            <div class="summary">
                <div class="header">
                    <h1>{invoice_data['company']['name']}</h1>
                    <h2>Invoice #{invoice_data['invoice_number']}</h2>
                </div>
                
                <p><strong>Bill To:</strong> {invoice_data['customer']['company_name']}</p>
                <p><strong>Due Date:</strong> {datetime.fromisoformat(invoice_data['due_date']).strftime('%B %d, %Y')}</p>
                <p><strong>Amount Due:</strong> <span class="amount">${invoice_data['amounts']['total_amount']:,.2f}</span></p>
                
                <p>Thank you for your business!</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def save_invoice_pdf(self, invoice_html: str, output_path: str) -> str:
        """Save invoice as PDF (requires external PDF library)"""
        
        # This would typically use a library like weasyprint or pdfkit
        # For now, return the HTML
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(invoice_html)
        
        return output_path
    
    def update_settings(self, settings: InvoiceSettings):
        """Update invoice settings"""
        self.invoice_settings = settings
    
    def add_tax_rate(self, jurisdiction: str, tax_item: TaxItem):
        """Add or update tax rate for a jurisdiction"""
        self.tax_rates[jurisdiction] = tax_item
    
    def get_invoice_preview(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get invoice preview data"""
        
        return {
            'preview_id': str(uuid.uuid4()),
            'invoice_number': invoice_data['invoice_number'],
            'customer_name': invoice_data['customer']['company_name'],
            'due_date': invoice_data['due_date'],
            'total_amount': invoice_data['amounts']['total_amount'],
            'currency': invoice_data['amounts']['currency'],
            'line_item_count': len(invoice_data['line_items']),
            'has_overages': any(item['is_overage'] for item in invoice_data['line_items']),
            'tax_amount': invoice_data['amounts']['tax_total'],
            'payment_terms': invoice_data['payment_terms']['name']
        }