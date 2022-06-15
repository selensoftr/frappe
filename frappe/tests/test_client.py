# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors

import unittest

import frappe


class TestClient(unittest.TestCase):
	def test_set_value(self):
		todo = frappe.get_doc(dict(doctype="ToDo", description="test")).insert()
		frappe.set_value("ToDo", todo.name, "description", "test 1")
		self.assertEqual(frappe.get_value("ToDo", todo.name, "description"), "test 1")

		frappe.set_value("ToDo", todo.name, {"description": "test 2"})
		self.assertEqual(frappe.get_value("ToDo", todo.name, "description"), "test 2")

	def test_delete(self):
		from frappe.client import delete

		todo = frappe.get_doc(dict(doctype="ToDo", description="description")).insert()
		delete("ToDo", todo.name)

		self.assertFalse(frappe.db.exists("ToDo", todo.name))
		self.assertRaises(frappe.DoesNotExistError, delete, "ToDo", todo.name)

	def test_http_valid_method_access(self):
		from frappe.client import delete
		from frappe.handler import execute_cmd

		frappe.set_user("Administrator")

		frappe.local.request = frappe._dict()
		frappe.local.request.method = "POST"

		frappe.local.form_dict = frappe._dict(
			{"doc": dict(doctype="ToDo", description="Valid http method"), "cmd": "frappe.client.save"}
		)
		todo = execute_cmd("frappe.client.save")

		self.assertEqual(todo.get("description"), "Valid http method")

		delete("ToDo", todo.name)

	def test_http_invalid_method_access(self):
		from frappe.handler import execute_cmd

		frappe.set_user("Administrator")

		frappe.local.request = frappe._dict()
		frappe.local.request.method = "GET"

		frappe.local.form_dict = frappe._dict(
			{"doc": dict(doctype="ToDo", description="Invalid http method"), "cmd": "frappe.client.save"}
		)

		self.assertRaises(frappe.PermissionError, execute_cmd, "frappe.client.save")

	def test_run_doc_method(self):
		from frappe.handler import execute_cmd

		if not frappe.db.exists("Report", "Test Run Doc Method"):
			report = frappe.get_doc(
				{
					"doctype": "Report",
					"ref_doctype": "User",
					"report_name": "Test Run Doc Method",
					"report_type": "Query Report",
					"is_standard": "No",
					"roles": [{"role": "System Manager"}],
				}
			).insert()
		else:
			report = frappe.get_doc("Report", "Test Run Doc Method")

		frappe.local.request = frappe._dict()
		frappe.local.request.method = "GET"

		# Whitelisted, works as expected
		frappe.local.form_dict = frappe._dict(
			{
				"dt": report.doctype,
				"dn": report.name,
				"method": "toggle_disable",
				"cmd": "run_doc_method",
				"args": 0,
			}
		)

		execute_cmd(frappe.local.form_dict.cmd)

		# Not whitelisted, throws permission error
		frappe.local.form_dict = frappe._dict(
			{
				"dt": report.doctype,
				"dn": report.name,
				"method": "create_report_py",
				"cmd": "run_doc_method",
				"args": 0,
			}
		)

		self.assertRaises(frappe.PermissionError, execute_cmd, frappe.local.form_dict.cmd)

	def test_array_values_in_request_args(self):
		import requests

		from frappe.auth import CookieManager, LoginManager

		frappe.utils.set_request(path="/")
		frappe.local.cookie_manager = CookieManager()
		frappe.local.login_manager = LoginManager()
		frappe.local.login_manager.login_as("Administrator")
		params = {
			"doctype": "DocType",
			"fields": ["name", "modified"],
			"sid": frappe.session.sid,
		}
		headers = {
			"accept": "application/json",
			"content-type": "application/json",
		}
		url = (
			f"http://{frappe.local.site}:{frappe.conf.webserver_port}/api/method/frappe.client.get_list"
		)
		res = requests.post(url, json=params, headers=headers)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		first_item = data["message"][0]
		self.assertTrue("name" in first_item)
		self.assertTrue("modified" in first_item)
		frappe.local.login_manager.logout()

	def test_client_get(self):
		from frappe.client import get

		todo = frappe.get_doc(doctype="ToDo", description="test").insert()
		filters = {"name": todo.name}
		filters_json = frappe.as_json(filters)

		self.assertEqual(get("ToDo", filters=filters).description, "test")
		self.assertEqual(get("ToDo", filters=filters_json).description, "test")

		todo.delete()

	def test_client_insert(self):
		from frappe.client import insert

		def get_random_title():
			return "test-{0}".format(frappe.generate_hash())

		# test insert dict
		doc = {"doctype": "Note", "title": get_random_title(), "content": "test"}
		note1 = insert(doc)
		self.assertTrue(note1)

		# test insert json
		doc["title"] = get_random_title()
		json_doc = frappe.as_json(doc)
		note2 = insert(json_doc)
		self.assertTrue(note2)

		# test insert child doc without parent fields
		child_doc = {"doctype": "Note Seen By", "user": "Administrator"}
		with self.assertRaises(frappe.ValidationError):
			insert(child_doc)

		# test insert child doc with parent fields
		child_doc = {
			"doctype": "Note Seen By",
			"user": "Administrator",
			"parenttype": "Note",
			"parent": note1.name,
			"parentfield": "seen_by",
		}
		note3 = insert(child_doc)
		self.assertTrue(note3)

		# cleanup
		frappe.delete_doc("Note", note1.name)
		frappe.delete_doc("Note", note2.name)

	def test_client_insert_many(self):
		from frappe.client import insert, insert_many

		def get_random_title():
			return "test-{0}".format(frappe.generate_hash(length=5))

		# insert a (parent) doc
		note1 = {"doctype": "Note", "title": get_random_title(), "content": "test"}
		note1 = insert(note1)

		doc_list = [
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{"doctype": "Note", "title": get_random_title(), "content": "test"},
			{"doctype": "Note", "title": get_random_title(), "content": "test"},
		]

		# insert all docs
		docs = insert_many(doc_list)

		# make sure only 1 name is returned for the parent upon insertion of child docs
		self.assertEqual(len(docs), 3)
		self.assertIn(note1.name, docs)

		# cleanup
		for doc in docs:
			frappe.delete_doc("Note", doc)
