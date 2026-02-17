import frappe

def _nepali_in_words(integer: int) -> str:
	"""
	Manual Nepali number to words conversion using Arba/Kharba system.
	Handles numbers up to 9,999,999,999,999 (99 Kharba).
	"""
	if integer < 0:
		return "Minus " + _nepali_in_words(-integer)

	ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
	teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", 
	         "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
	tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
	
	def words_below_hundred(n):
		"""
		Convert an integer from 0 to 99 into its English word representation.

		:param n: Integer value between 0 and 99 inclusive.
		:return: English words for `n`; returns an empty string when `n` is 0.
		"""
		if n == 0:
			return ""
		elif n < 10:
			return ones[n]
		elif n < 20:
			return teens[n - 10]
		else:
			return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
	
	if integer == 0:
		return "Zero"
	
	result = []
	
	# Kharba (खर्ब) = 10^11
	if integer >= 100000000000:
		kharba = integer // 100000000000
		result.append(words_below_hundred(kharba) + " Kharba")
		integer %= 100000000000
	
	# Arba (अर्ब) = 10^9
	if integer >= 1000000000:
		arba = integer // 1000000000
		result.append(words_below_hundred(arba) + " Arba")
		integer %= 1000000000
	
	# Crore = 10^7
	if integer >= 10000000:
		crore = integer // 10000000
		result.append(words_below_hundred(crore) + " Crore")
		integer %= 10000000
	
	# Lakh = 10^5
	if integer >= 100000:
		lakh = integer // 100000
		result.append(words_below_hundred(lakh) + " Lakh")
		integer %= 100000
	
	# Thousand
	if integer >= 1000:
		thousand = integer // 1000
		result.append(words_below_hundred(thousand) + " Thousand")
		integer %= 1000
	
	# Hundreds
	if integer >= 100:
		hundred = integer // 100
		result.append(ones[hundred] + " Hundred")
		integer %= 100
	
	# Remainder (below 100)
	if integer > 0:
		result.append(words_below_hundred(integer))
	
	return " ".join(result)


# Override function that replaces Frappe's core in_words function
def in_words(integer: int, in_million=True) -> str:
	"""
	Returns string in words for the given integer.
	"""
	from num2words import num2words

	if not in_million:
		# Check if currency is NPR (Nepalese Rupee)
		try:
			defaults = frappe.defaults.get_defaults()
			currency = defaults.get("currency")
			country = defaults.get("country")
			if currency == "NPR" or country == "Nepal":
				return _nepali_in_words(int(integer))
		except Exception as exc:
			frappe.log_error(exc, "Error determining currency/country in nepali_num2words.in_words")
		
		locale = "en_IN"
	else:
		locale = getattr(frappe.local, "lang", None) or "en"

	integer = int(integer)
	try:
		ret = num2words(integer, lang=locale)
	except (NotImplementedError, OverflowError):
		ret = num2words(integer, lang="en")
	return ret.replace("-", " ")