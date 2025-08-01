import frappe

def cleanup_salary_structures():
    companies = frappe.get_all("Company", fields=["name"])
    patterns = [
        "Salary Structure Unmarried - EPF - ",
        "Salary Structure Married - EPF - ",
        "Salary Structure Unmarried - SSF - ",
        "Salary Structure Married - SSF - ",
    ]
    deleted = []
    for company in companies:
        for pattern in patterns:
            full_name = f"{pattern}{company.name}"
            structure_name = frappe.db.get_value(
                "Salary Structure", {"name": full_name, "docstatus": 0}
            )
            if structure_name:
                try:
                    frappe.delete_doc(
                        "Salary Structure",
                        structure_name,
                        force=True,
                        ignore_permissions=True,
                    )
                    deleted.append(full_name)
                except Exception as e:
                    frappe.logger().error(
                        f"Failed to delete Salary Structure {full_name}: {str(e)}"
                    )

    if deleted:
        frappe.logger().info(f"Deleted Salary Structures: {', '.join(deleted)}")
    else:
        frappe.logger().info("No Salary Structures deleted (either not found or already submitted)")
