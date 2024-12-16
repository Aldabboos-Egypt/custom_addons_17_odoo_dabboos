# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import datetime
import io
import json
import logging
import math
import re
import base64
from ast import literal_eval
from collections import defaultdict
from functools import cmp_to_key

import markupsafe
from babel.dates import get_quarter_names
from dateutil.relativedelta import relativedelta

from odoo.addons.web.controllers.utils import clean_action
from odoo import models, fields, api, _, osv, _lt
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import config, date_utils, get_lang, float_compare, float_is_zero
from odoo.tools.float_utils import float_round
from odoo.tools.misc import formatLang, format_date, xlsxwriter
from odoo.tools.safe_eval import expr_eval, safe_eval
from odoo.models import check_method_name
from itertools import groupby

_logger = logging.getLogger(__name__)

class AccountReport(models.Model):
    _inherit = 'account.report'

    
    @api.model
    def format_value(self, options, value, currency=False, blank_if_zero=False, figure_type=None, digits=1):
        """ Formats a value for display in a report (not especially numerical). figure_type provides the type of formatting we want.
        """
        if value is None:
            return ''

        if figure_type == 'none':
            return value

        if isinstance(value, str) or figure_type == 'string':
            return str(value)

        if figure_type == 'monetary':
            if options.get('multi_currency'):
                digits = None
                
                # currency = currency or self.env.company.currency_id
            else:
                digits = (currency or self.env.company.currency_id).decimal_places
                currency = None
           
        elif figure_type == 'integer':
            currency = None
            digits = 0
        elif figure_type == 'boolean':
            return _("Yes") if bool(value) else _("No")
        elif figure_type in ('date', 'datetime'):
            return format_date(self.env, value)
        else:
            currency = None

        if self.is_zero(value, currency=currency, figure_type=figure_type, digits=digits):
            if blank_if_zero:
                return ''
            value = abs(value)

        if self._context.get('no_format'):
            return value
        
        remain = value - math.trunc(value)
        remain = math.trunc(remain*100)
      
        if remain > 0 and remain%10 > 0:
            
            formatted_amount = formatLang(self.env, value, currency_obj=currency, digits=2)
        elif remain > 0 and remain%10 == 0:
           
            formatted_amount = formatLang(self.env, value, currency_obj=currency, digits=1)
        else:
            formatted_amount = formatLang(self.env, value, currency_obj=currency, digits=0)
            

        if digits == None:
        
            formatted_amount = self.env.company.currency_id.symbol + '' + str(formatted_amount)
            
        # formatted_amount = formatLang(self.env, value, currency_obj=currency, digits=digits)

        if figure_type == 'percentage':
            return f"{formatted_amount}%"

        return formatted_amount