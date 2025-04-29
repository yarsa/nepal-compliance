# Manual Install - Nepal Compliance
**This guide will help you to manually install and run Nepal Compliance app in your Frappe environment.**

### Dependencies
* A CLI utility `frappe-bench` installed and initialized. Check using `bench --version`
* An active Frappe `site` created and working. Check using `bench list-sites`

```
MariaDB 10.6.6+                               (11.3 is recommended on develop)
Python 3.10/11/12
Node 18 or 20
Redis 6                                       (caching and realtime updates)
yarn 1.12+                                    (js dependency manager)
pip 20+                                       (py dependency manager)
wkhtmltopdf (version 0.12.5 with patched qt)  (for pdf generation)
cron                                          (bench's scheduled jobs: automated certificate renewal, scheduled backups)
```
For detailed pre-requisites and installation, refer to the [Frappe’s official documentation](https://docs.frappe.io/framework/user/en/installation).

Nepal Compliance app is built on top of ERPNext and HRMS. Ensure that both are installed and running before installing or using this app.

**Ensure you are inside a working bench directory with `bench find .`**

First, start bench server:
```
bench start
```
Keep the bench server running in the first terminal and open a second terminal to run commands ahead.

## Step 1: Install ERPNext
First, Get ERPNext from Frappe's App Registry

```
bench get-app erpnext
```

Second, Install ERPNext on your site:

```
bench --site your_site_name install-app erpnext
```

## Step 2: Install HRMS
First, Get HRMS from Frappe's App Registry

```
bench get-app hrms
```

Second, Install HRMS on your site:

```
bench --site your_site_name install-app hrms
```

## Step 3: Install Nepal Compliance
First, Get the Nepal Compliance app:

```
bench get-app https://github.com/yarsa/nepal-compliance.git
```

Install Nepal Compliance on your site:

```
bench --site your_site_name install-app nepal_compliance
```

**To verify the installation,**
```
bench --site your_site_name list-apps
```
You should see `nepal_compliance` listed as installed apps on your site.

### Access your ERP instance running at `http://localhost:8000`

In cases of no visible changes, run bench migrations on the site to apply changes.
```
bench --site your_site_name migrate
```

---
# Next
* Learn how to [contribute to this project](/CONTRIBUTING.md)
* [Docker Install - Nepal Compliance](/docs/docker-install.md)

**If you liked our work, then we would love to get your stars on our GitHub and Docker repositories.** 😀
