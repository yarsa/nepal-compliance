function replaceCustomWorkspaceIcon() {
    const customIconPath = "/assets/nepal_compliance/icon/nepal-compliance.svg";
    const targetHref = `#icon-${customIconPath}`;
  
    document.querySelectorAll('svg.icon use').forEach((useTag) => {
      const href = useTag.getAttribute('href');
      if (href === targetHref) {
        const svg = useTag.closest('svg');
        const container = svg?.closest('.sidebar-item-icon');
        if (container && !container.querySelector('img')) {
          container.innerHTML = `<img src="${customIconPath}" style="width: 20px; height: 20px; margin-right: 10px;" />`;
        }
      }
    });
  }
  
  frappe.after_ajax(() => {
    setTimeout(replaceCustomWorkspaceIcon, 1000);
  });
  
  frappe.router.on('change', () => {
    setTimeout(replaceCustomWorkspaceIcon, 1000);
  });  