app_name = "yarsa"
app_title = "Yarsa"
app_publisher = "yarsa"
app_description = "For Customization "
app_email = "yarsa@gmail.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/yarsa/css/yarsa.css"
# app_include_js = "/assets/yarsa/js/yarsa.js"

# include js, css files in header of web template
# web_include_css = "/assets/yarsa/css/yarsa.css"
# web_include_js = "/assets/yarsa/js/yarsa.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "yarsa/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_js = {"Salary Slip" : "public/js/salary_slip.js"}
doctype_js = {"Salary Component": "public/js/salary_component.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "yarsa/public/icons.svg"

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
# 	"methods": "yarsa.utils.jinja_methods",
# 	"filters": "yarsa.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "yarsa.install.before_install"
before_install = "yarsa.install.install"
# after_install = "yarsa.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "yarsa.uninstall.before_uninstall"]
before_uninstall = "yarsa.uninstaall.delete_salary_component"
# after_uninstall = "yarsa.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "yarsa.utils.before_app_install"
# after_app_install = "yarsa.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "yarsa.utils.before_app_uninstall"
# after_app_uninstall = "yarsa.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "yarsa.notifications.get_notification_config"

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
#     "Out Of Office Slip": {
#         "on_update": "yarsa.custom_code.out_of_office.on_update"
#     },
#     "Employee": {
#         "on_update": "yarsa.custom_code.employee_id_card.get_context"
#     }
# }
# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"yarsa.tasks.all"
# 	],
# 	"daily": [
# 		"yarsa.tasks.daily"
# 	],
# 	"hourly": [
# 		"yarsa.tasks.hourly"
# 	],
# 	"weekly": [
# 		"yarsa.tasks.weekly"
# 	],
# 	"monthly": [
# 		"yarsa.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "yarsa.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "yarsa.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "yarsa.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["yarsa.utils.before_request"]
# after_request = ["yarsa.utils.after_request"]

# Job Events
# ----------
# before_job = ["yarsa.utils.before_job"]
# after_job = ["yarsa.utils.after_job"]

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
# 	"yarsa.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

