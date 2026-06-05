import frappe
from frappe import _
from frappe.model.document import Document
from datetime import timedelta


class SocialMediaPostCycle(Document):

	def on_update(self):
		prev = self.get_doc_before_save()
		prev_state = prev.workflow_state if prev else None
		curr_state = self.workflow_state

		if prev_state == curr_state:
			return

		if curr_state == "Post Completed":
			self._on_post_completed()
		elif curr_state == "Engagement Acknowledged":
			self._on_engagement_acknowledged()
		elif curr_state == "Monitoring":
			self._on_monitoring_started()

	def _on_post_completed(self):
		frappe.db.set_value(
			self.doctype, self.name, "posted_at", frappe.utils.now_datetime()
		)
		# Notify Founder via email and desk notification
		founders = _get_users_with_role("Founder")
		if not founders:
			return
		doc_link = _doc_url(self.name)
		frappe.sendmail(
			recipients=founders,
			subject=f"Action Required: Like & Share — {self.post_title}",
			message=f"""
				<p>Hi,</p>
				<p>The Digital Marketing Manager has completed a social media post and it is now live.</p>
				<table>
					<tr><td><b>Post Title</b></td><td>{self.post_title}</td></tr>
					<tr><td><b>Platform</b></td><td>{self.platform or "—"}</td></tr>
					<tr><td><b>Post URL</b></td><td>{self.post_url or "—"}</td></tr>
				</table>
				<p>Please <b>Like and Share</b> this post on LinkedIn, then click
				<b>Acknowledge Share</b> inside the record to trigger Intern monitoring.</p>
				<p><a href="{doc_link}">Open Post Cycle Record</a></p>
			""",
			now=True,
		)
		_desk_notify(
			founders,
			f"Please Like & Share on LinkedIn: {self.post_title}",
		)

	def _on_engagement_acknowledged(self):
		now = frappe.utils.now_datetime()
		frappe.db.set_value(
			self.doctype,
			self.name,
			{"engagement_acknowledged_at": now, "acknowledged_by": frappe.session.user},
		)
		# Notify Interns to begin monitoring
		interns = _get_users_with_role("Intern")
		if not interns:
			return
		doc_link = _doc_url(self.name)
		frappe.sendmail(
			recipients=interns,
			subject=f"Begin Analytics Monitoring — {self.post_title}",
			message=f"""
				<p>Hi,</p>
				<p>The team has liked and shared the post. Your monitoring period has started.</p>
				<table>
					<tr><td><b>Post Title</b></td><td>{self.post_title}</td></tr>
					<tr><td><b>Platform</b></td><td>{self.platform or "—"}</td></tr>
					<tr><td><b>Engagement Start</b></td><td>{now.strftime("%Y-%m-%d %H:%M")}</td></tr>
				</table>
				<p>You will receive automated reminders at <b>1 hour</b> and <b>24 hours</b>
				to submit your analytics report.</p>
				<p><a href="{doc_link}">Open Post Cycle Record</a></p>
			""",
			now=True,
		)
		_desk_notify(
			interns,
			f"Analytics monitoring started for: {self.post_title}. Reminders at 1h and 24h.",
		)

	def _on_monitoring_started(self):
		# Triggered by Intern clicking "Start Monitoring" — no extra action needed
		# The scheduled task handles the timed alerts from engagement_acknowledged_at
		pass


# ---------------------------------------------------------------------------
# Scheduled task — runs hourly via scheduler_events
# ---------------------------------------------------------------------------

def send_analytics_reminders():
	"""Check all active post cycles and fire 1h / 24h analytics alerts."""
	now = frappe.utils.now_datetime()

	posts = frappe.get_all(
		"Social Media Post Cycle",
		filters={
			"workflow_state": ["in", ["Engagement Acknowledged", "Monitoring"]],
		},
		fields=[
			"name",
			"post_title",
			"platform",
			"engagement_acknowledged_at",
			"one_hour_alert_sent",
			"twenty_four_hour_alert_sent",
		],
	)

	for post in posts:
		ack_time = post.get("engagement_acknowledged_at")
		if not ack_time:
			continue

		elapsed = now - ack_time
		updates = {}

		if not post.one_hour_alert_sent and elapsed >= timedelta(hours=1):
			_send_analytics_alert(post.name, post.post_title, post.platform, "1 Hour")
			updates["one_hour_alert_sent"] = 1
			updates["one_hour_alert_sent_at"] = now

		if not post.twenty_four_hour_alert_sent and elapsed >= timedelta(hours=24):
			_send_analytics_alert(post.name, post.post_title, post.platform, "24 Hours")
			updates["twenty_four_hour_alert_sent"] = 1
			updates["twenty_four_hour_alert_sent_at"] = now

		if updates:
			frappe.db.set_value("Social Media Post Cycle", post.name, updates)


def _send_analytics_alert(post_name, post_title, platform, interval):
	interns = _get_users_with_role("Intern")
	if not interns:
		return
	doc_link = _doc_url(post_name)
	frappe.sendmail(
		recipients=interns,
		subject=f"[{interval} Report Due] {post_title}",
		message=f"""
			<p>Hi,</p>
			<p>It has been <b>{interval}</b> since the team engaged with the post.
			Please submit your analytics report now.</p>
			<table>
				<tr><td><b>Post</b></td><td>{post_title}</td></tr>
				<tr><td><b>Platform</b></td><td>{platform or "—"}</td></tr>
			</table>
			<p>Open the record and fill in the <b>{interval} Performance Report</b> field.</p>
			<p><a href="{doc_link}">Submit Analytics Report</a></p>
		""",
		now=False,  # queued so it doesn't block the scheduler
	)
	_desk_notify(
		interns,
		f"[{interval} Alert] Submit analytics report for: {post_title}",
	)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_users_with_role(role):
	return frappe.get_all(
		"Has Role",
		filters={"role": role, "parenttype": "User"},
		pluck="parent",
	)


def _doc_url(name):
	return f"{frappe.utils.get_url()}/app/social-media-post-cycle/{name}"


def _desk_notify(users, message):
	for user in users:
		frappe.publish_realtime(
			event="msgprint",
			message=message,
			user=user,
		)
