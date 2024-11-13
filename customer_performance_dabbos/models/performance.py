import base64
from datetime import datetime, timedelta
from io import BytesIO

import xlsxwriter
from odoo import models, fields


class PartnerPerformanceWizard(models.TransientModel):
    _name = 'partner.performance.wizard'


    partner_ids= fields.Many2many(
        comodel_name='res.partner', required=True,
        string='Partners')

    file_name = fields.Char(
        string='File_name',
        required=False)
    file = fields.Binary(string="", )

    def get_invoices_by_month(self, partner_id):

        invoice_obj = self.env['account.move'].sudo().search(['&','&',
            ('partner_id', '=', partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),

        ])


        invoices_by_month = {}
        for invoice in invoice_obj:
            month = invoice.date.strftime('%Y-%m')  # Group by year and month
            if invoice.amount_total_signed:

                if month in invoices_by_month:
                    invoices_by_month[month][0] += 1
                    invoices_by_month[month][1] += invoice.amount_total_signed
                else:
                    invoices_by_month[month] = [1, invoice.amount_total_signed]

        return {month: data for month, data in invoices_by_month.items()}

    def get_payments_by_month(self, partner_id):
        # Initialize an empty dictionary to store payments data
        payments_by_month = {}



        # Query account.move.line for payments
        print("p",partner_id)
        payments = self.env['account.move.line'].search(['&','&',
            ('account_id', '=',partner_id.property_account_receivable_id.id),
            ('partner_id', '=', partner_id.id),
            ('move_id.state', '=', 'posted'),

        ])


        result_dict = {}
        for payment in payments:
            month = payment.date.strftime('%Y-%m')  # Group by year and month
            if payment.credit:
                if month in result_dict:
                    result_dict[month][0] += 1
                    result_dict[month][1] += payment.credit
                else:
                    result_dict[month] = [1, payment.credit]

        return {month: data for month, data in result_dict.items()}




    def generate_report(self):
        # Get list of partners
        partners = self.partner_ids

        # Setup workbook
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Define cell formats
        header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        body_format = workbook.add_format(
            {'border': 1, 'align': 'center', 'valign': 'vcenter', 'bold': True, 'text_wrap': True})
        data_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        customer_format = workbook.add_format({'align': 'center', 'bold': True, 'underline': True})

        # Set column width for better readability
        worksheet.set_column('A:A', 18)
        worksheet.set_column('B:C', 12)
        worksheet.set_column('D:E', 15)
        worksheet.set_column('F:F', 18)
        worksheet.set_column('G:H', 20)

        # Write headers with formatting
        headers = ["Customer", "Month", "Inv Count", "Inv Total", "Avg Inv", "Payment", "Avg Payment", "Balance"]
        worksheet.write_row(0, 0, headers, header_format)

        # Write data in one go per row with formatting
        row = 1
        for partner in partners:

            # Fetch data with SQL
            invoices_by_month = self.get_invoices_by_month(partner)
            payments_by_month = self.get_payments_by_month(partner)

            if invoices_by_month and payments_by_month:
                pass
            else:
                continue

            balance = 0
            counter = 0
            total_payment =total_invoice=  0.0
            invoice_count =payment_count= 0

            if len(payments_by_month) > len(invoices_by_month):
                loop_lenth=payments_by_month
            else:
                loop_lenth=invoices_by_month


            for month in sorted(loop_lenth):

                print(invoices_by_month)
                print(month)
                if month not in invoices_by_month:
                    invoices_by_month[month]=[0,0.0]

                if month not in payments_by_month:
                    payments_by_month[month]=[0, 0.0]


                invoice_data = invoices_by_month[month]
                payment_data = payments_by_month[month]
                print("invoice" ,invoice_data)
                print("Payment" ,payment_data)

                avg_invoice = invoice_data[1] / invoice_data[0] if invoice_data[0] else 0
                avg_payment = payment_data[1] / payment_data[0] if payment_data[0] else 0

                # balance += invoice_data[1] - payment_data

                data = [partner.name, month, invoice_data[0], invoice_data[1], round(avg_invoice, 2), payment_data[1],
                         ]
                worksheet.write_row(row, 0, data, data_format)
                row += 1
                counter += 1
                invoice_count += invoice_data[0]
                total_invoice += invoice_data[1]
                payment_count += payment_data[0]
                total_payment += payment_data[1]

            # Add totals with formatting
            # total_payment = sum(payments_by_month.values())


            avg_payment = total_payment / len(payments_by_month)
            total_invoice_avg = total_invoice / invoice_count

            worksheet.write_formula(row, 3, '=SUM(D{}:D{})'.format(row - invoice_count, row - 1),
                                    header_format)  # total inv
            worksheet.write(row, 0, "Total", header_format)
            worksheet.write(row, 1, len(invoices_by_month), header_format)
            worksheet.write(row, 2, invoice_count, header_format)
            worksheet.write(row, 3, round(total_invoice, 2), header_format)
            worksheet.write(row, 4, round(total_invoice_avg, 2), header_format)
            worksheet.write(row, 5, round(total_payment, 2), header_format)
            worksheet.write(row, 6, round(avg_payment, 2), header_format)
            worksheet.write(row, 7,  partner.credit -partner.debit , header_format)

            row += 2

        # Set the border for the table
        worksheet.conditional_format('A1:H{}'.format(row),
                                     {'type': 'no_blanks', 'format': body_format})
        worksheet.conditional_format('A1:H1',
                                     {'type': 'no_blanks', 'format': header_format})

        # Close and return XLSX file
        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())
        self.write({
            'file_name': 'Customer Performance.xlsx',
            'file': file_data
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"web/content/?model={self._name}&id={self.id}&filename_field=file_name&field=file&download=true&filename=Customer Performance.xlsx",
            'target': 'self',
        }