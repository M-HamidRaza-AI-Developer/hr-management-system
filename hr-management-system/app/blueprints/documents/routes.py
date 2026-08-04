import os
import uuid

from flask import render_template, redirect, url_for, flash, request, send_file, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.blueprints.documents import bp
from app.extensions import db
from app.decorators import roles_required, self_or_roles_required
from app.models.document import Document, DocumentType
from app.models.employee import Employee
from app.models.user import Role
from app.utils.audit import log_action


def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


@bp.route("/employee/<int:employee_id>")
@login_required
@self_or_roles_required(lambda employee_id: employee_id, Role.ADMIN, Role.HR)
def list_documents(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    return render_template("documents/list.html", employee=employee)


@bp.route("/employee/<int:employee_id>/upload", methods=["POST"])
@login_required
@self_or_roles_required(lambda employee_id: employee_id, Role.ADMIN, Role.HR)
def upload(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    file = request.files.get("file")
    doc_type = request.form.get("document_type", DocumentType.OTHER.value)

    if not file or file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("documents.list_documents", employee_id=employee_id))

    if not _allowed_file(file.filename):
        flash("File type not allowed.", "danger")
        return redirect(url_for("documents.list_documents", employee_id=employee_id))

    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit(".", 1)[-1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "documents")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, stored_filename)
    file.save(filepath)

    document = Document(
        employee_id=employee.id,
        document_type=DocumentType(doc_type),
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_size_bytes=os.path.getsize(filepath),
        uploaded_by_id=current_user.id,
    )
    db.session.add(document)
    db.session.flush()
    log_action("document.upload", "Document", document.id, {"employee_id": employee.id})
    db.session.commit()

    flash("Document uploaded.", "success")
    return redirect(url_for("documents.list_documents", employee_id=employee_id))


@bp.route("/<int:document_id>/download")
@login_required
@self_or_roles_required(
    lambda document_id: Document.query.get_or_404(document_id).employee_id, Role.ADMIN, Role.HR
)
def download(document_id):
    document = Document.query.get_or_404(document_id)
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "documents")
    filepath = os.path.join(upload_dir, document.stored_filename)
    if not os.path.exists(filepath):
        abort(404)
    return send_file(filepath, as_attachment=True, download_name=document.original_filename)


@bp.route("/<int:document_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.HR)
def delete(document_id):
    document = Document.query.get_or_404(document_id)
    employee_id = document.employee_id
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "documents")
    filepath = os.path.join(upload_dir, document.stored_filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    log_action("document.delete", "Document", document.id)
    db.session.delete(document)
    db.session.commit()
    flash("Document deleted.", "info")
    return redirect(url_for("documents.list_documents", employee_id=employee_id))
