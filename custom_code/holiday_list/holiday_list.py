import frappe 
from frappe import _, throw
from frappe.utils import formatdate, getdate, today
from frappe.model.document import Document

class HolidayList_Nepali_Date(Document):

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from erpnext.setup.doctype.holiday.holiday import Holiday

		color: DF.Color | None
		country: DF.Autocomplete | None
		# from_date: DF.Date
		holiday_list_name: DF.Data
		holidays: DF.Table[Holiday]
		subdivision: DF.Autocomplete | None
		# to_date: DF.
		total_holidays: DF.Int
		weekly_off: DF.Literal[
			"", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
		]
        nepali_from_date: DF.Data
        nepali_to_date: DF.Data
	def validate(self):
		self.total_holidays = len(self.holidays)
		self.sort_holidays()

	@frappe.whitelist()
	def get_weekly_off_dates(self):
		if not self.weekly_off:
			throw(_("Please select weekly off day"))

		existing_holidays = self.get_holidays()

		for d in self.get_weekly_off_date_list(self.nepali_from_date, self.nepali_to_date):
			if d in existing_holidays:
				continue

			self.append("holidays", {"description": _(self.weekly_off), "holiday_date": d, "weekly_off": 1})
    def sort_holidays(self):
		self.holidays.sort(key=lambda x: getdate(x.holiday_date))
		for i in range(len(self.holidays)):
			self.holidays[i].idx = i + 1

	def get_holidays(self) -> list[date]:
		return [getdate(holiday.holiday_date) for holiday in self.holidays]
    