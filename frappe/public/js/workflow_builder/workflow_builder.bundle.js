import { createApp } from "vue";
import WorkflowBuilderComponent from "./WorkflowBuilder.vue";

class WorkflowBuilder {
	constructor({ wrapper, page, workflow }) {
		this.$wrapper = $(wrapper);
		this.page = page;
		this.workflow = workflow;

		this.init();
	}

	init() {
		// set page title
		this.page.set_title(__("Editing {0}", [this.workflow]));

		this.setup_app();
	}

	setup_app() {
		// create a vue instance
		let app = createApp(WorkflowBuilderComponent, { workflow: this.workflow });
		SetVueGlobals(app);
		app.use(pinia);

		// mount the app
		this.$workflow_builder = app.mount(this.$wrapper.get(0));
	}
}

frappe.provide("frappe.ui");
frappe.ui.WorkflowBuilder = WorkflowBuilder;
export default WorkflowBuilder;
