__version__ = "0.2.0"

# Monkey patch Frappe's in_words function to use Nepali number-to-words conversion
import frappe
import frappe.utils
import frappe.utils.data

def _apply_patches():
	try:
		from nepal_compliance.nepali_num2words import in_words
		frappe.utils.in_words = in_words
		frappe.utils.data.in_words = in_words
	except Exception as e:
		try:
			frappe.log_error(f"Failed to apply patches for Nepal Compliance: {e}", "Nepal Compliance Patch Error")
		except Exception:
			pass

# Apply patches on import
_apply_patches()