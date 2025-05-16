app_name = "nepal_compliance"
app_title = "Nepal Compliance"
app_publisher = "Yarsa Labs Pvt. Ltd."
app_description = "ERPNext app to comply with Nepali laws and regulations"
app_email = "support@yarsalabs.com"
app_license = "GNU General Public License (v3)"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "nepal_compliance",
# 		"logo": "/assets/nepal_compliance/logo.png",
# 		"title": "Nepal Compliance",
# 		"route": "/nepal_compliance",
# 		"has_permission": "nepal_compliance.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/nepal_compliance/css/nepal_compliance.css"
app_include_css = ["/assets/nepal_compliance/css/calendar.css",
                   "/assets/nepal_compliance/css/doctype.css"]
# app_include_js = "/assets/nepal_compliance/js/nepal_compliance.js"
app_include_js = [
                 "/assets/nepal_compliance/js/bs_module.js",
                 "/assets/nepal_compliance/js/report_filter.js",
                 "/assets/nepal_compliance/js/icon_patch.js"
                 ]

# include js, css files in header of web template
# web_include_css = "/assets/nepal_compliance/css/nepal_compliance.css"
# web_include_js = "/assets/nepal_compliance/js/nepal_compliance.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "nepal_compliance/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
    "Company": "public/js/validate.js",
    "Salary Slip" : "public/js/salary_slip.js",
    "Expense Claim": "public/js/bs_date.js",
    "Leave Application": "public/js/bs_date.js",
    "Holiday List": ["public/js/bs_date.js","public/js/holiday_list.js"],
    "Holiday": "public/js/holiday_list.js",
    "Leave Allocation": "public/js/bs_date.js",
    "Attendance": "public/js/bs_date.js",
    "Fiscal Year": "public/js/bs_date.js",
    "Stock Entry": "public/js/hrms_bs_date.js",
    "Material Request": "public/js/hrms_bs_date.js",
    "Purchase Invoice": ["public/js/bs_date.js", "public/js/validate.js", "public/js/email.js", "public/js/utils.js"],
    "Purchase Order": "public/js/bs_date.js","Purchase Receipt": "public/js/bs_date.js",
    "Sales Order": "public/js/bs_date.js","Delivery Note": "public/js/bs_date.js",
    "Sales Invoice": ["public/js/bs_date.js", "public/js/validate.js", "public/js/email.js", "public/js/utils.js"],
    "CBMS Settings": "nepal_compliance/doctype/cbms_settings/cbms_settings.js",
    "Payment Entry": "public/js/bs_date.js",
    "Journal Entry": "public/js/bs_date.js",
    "Supplier": "public/js/validate.js",
    "Customer": "public/js/validate.js",
    "Request for Quotation": "public/js/bs_date.js","Supplier Quotation": "public/js/bs_date.js", "Quotation": "public/js/bs_date.js",
    "Blanket Order": "public/js/bs_date.js",
    "Landed Cost Voucher": "public/js/bs_date.js",
    "Asset": "public/js/bs_date.js", "Asset Repair": "public/js/bs_date.js", "Asset Movement": "public/js/bs_date.js", "Asset Value Adjustment": "public/js/bs_date.js", "Asset Capitalization": "public/js/bs_date.js",
    "POS Opening Entry": "public/js/bs_date.js", "POS Closing Entry": "public/js/bs_date.js",
    "Loyalty Program": "public/js/bs_date.js", "Promotional Scheme": "public/js/bs_date.js", "Pricing Rule": "public/js/bs_date.js", "Coupon Code": "public/js/bs_date.js",
    "Serial No": "public/js/bs_date.js", "Batch": "public/js/bs_date.js",
    "Installation Note": "public/js/bs_date.js", "Stock Reconciliation": "public/js/bs_date.js", "Quality Inspection": "public/js/bs_date.js", "Quick Stock Balance": "public/js/bs_date.js",
    "Payroll Entry": "public/js/payroll_bs_date.js", "Income Tax Slab": "public/js/payroll_bs_date.js", "Payroll Period": "public/js/payroll_bs_date.js", "Salary Structure Assignment": ["public/js/payroll_bs_date.js", "public/js/single_doc.js"], "Salary Withholding": "public/js/payroll_bs_date.js", "Additional Salary": "public/js/payroll_bs_date.js", "Employee Incentive": "public/js/payroll_bs_date.js", "Retention Bonus": "public/js/payroll_bs_date.js",
    "Employee Tax Exemption Proof Submission": "public/js/payroll_bs_date.js", "Employee Benefit Application": "public/js/payroll_bs_date.js", "Employee Benefit Claim": "public/js/hrms_bs_date.js",
    "Attendance Request": "public/js/hrms_bs_date.js", "Compensatory Leave Request": "public/js/hrms_bs_date.js", "Employee Advance": "public/js/hrms_bs_date.js", "Shift Assignment": "public/js/hrms_bs_date.js", "Shift Request": "public/js/hrms_bs_date.js", "Job Offer": "public/js/hrms_bs_date.js", "Employee Referral": "public/js/hrms_bs_date.js", "Shift Assignment Tool": "public/js/hrms_bs_date.js", "Employee Attendance Tool": "public/js/hrms_bs_date.js",
    "Upload Attendance": "public/js/hrms_bs_date.js", "Leave Period": "public/js/hrms_bs_date.js", "Leave Policy Assignment": "public/js/hrms_bs_date.js", "Leave Control Panel": "public/js/hrms_bs_date.js", "Leave Encashment": "public/js/hrms_bs_date.js",
    "Bulk Salary Structure Assignment": "public/js/single_doc.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "nepal_compliance/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "nepal_compliance.utils.jinja_methods",
# 	"filters": "nepal_compliance.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "nepal_compliance.install.before_install"
after_install = "nepal_compliance.install.install"
after_sync = ["nepal_compliance.custom_code.payroll.salary_structure.create_salary_structures",
              "nepal_compliance.custom_code.leave_type.leave_type.setup_default_leave_types"]
# after_install = "nepal_compliance.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "nepal_compliance.uninstall.before_uninstall"
# after_uninstall = "nepal_compliance.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "nepal_compliance.utils.before_app_install"
# after_app_install = "nepal_compliance.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "nepal_compliance.utils.before_app_uninstall"
# after_app_uninstall = "nepal_compliance.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "nepal_compliance.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }
doc_events = {

    "*": {
        "validate": "nepal_compliance.backdated_doctype_restriction.validate_backdate_and_sequence"
    },
    "Purchase Invoice" : {
        "on_trash": "nepal_compliance.utils.prevent_invoice_deletion",
        "on_submit": ["nepal_compliance.qr_code.create_qr_code", "nepal_compliance.email_utils.send_email_on_submit"]
    },
    "Sales Invoice" : {
        "on_submit": ["nepal_compliance.cbms_api.post_sales_invoice_or_return_to_cbms", "nepal_compliance.qr_code.create_qr_code", "nepal_compliance.email_utils.send_email_on_submit",
        ]
    }
}
# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"nepal_compliance.tasks.all"
# 	],
# 	"daily": [
# 		"nepal_compliance.tasks.daily"
# 	],
# 	"hourly": [
# 		"nepal_compliance.tasks.hourly"
# 	],
# 	"weekly": [
# 		"nepal_compliance.tasks.weekly"
# 	],
# 	"monthly": [
# 		"nepal_compliance.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "nepal_compliance.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "nepal_compliance.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "nepal_compliance.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["nepal_compliance.utils.before_request"]
# after_request = ["nepal_compliance.utils.after_request"]

# Job Events
# ----------
# before_job = ["nepal_compliance.utils.before_job"]
# after_job = ["nepal_compliance.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"nepal_compliance.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
     {
        "dt": "Custom Field",
        "filters": [
            [
               "module", "in", ["nepal_compliance"]
            ]
        ]
    },
    {
        "doctype": "Salary Component",
        "filters": [
            ["name", "in", ["Basic Salary", "Other Allowance", "Income Tax Unmarried", "Overtime", "Gratuity", "Earning Adjustment", "Deduction Adjustment",
                            "Employer's Contribution SSF Deduction", "Insurance", "CIT", "Employee's Contribution SSF", "Employer's Contribution SSF",
                            "Grade Amount", "Income Tax Married", "Income Tax Unmarried", "Provident Fund Employer", "Provident Fund Employee", "Leave and Late Deduction",
                            "Provident Fund Employer Deduction", "Gratuity Deduction"]]
        ]
    },
    {
        "doctype": "Leave Type",
        "filters": [
            ["name", "in", ["Annual Sick Leave", "Home Leave"]]
        ]
    }
]

purchase_sales = ["Purchase Invoice", "Sales Invoice"]

doctype_lists = ["Asset","Asset Capitalization","Asset Repair","Dunning","Invoice Discounting","Journal Entry",
                 "Landed Cost Voucher","Payment Entry","Period Closing Voucher","Process Deferred Accounting","Purchase Invoice",
                 "Purchase Receipt","POS Invoice","Sales Invoice","Stock Entry","Stock Reconciliation","Subcontracting Receipt",]