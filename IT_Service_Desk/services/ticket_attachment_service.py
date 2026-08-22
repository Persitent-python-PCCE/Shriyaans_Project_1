import os
import uuid

from werkzeug.utils import secure_filename

from models.ticket_attachment import TicketAttachment

from dao.ticket_attachment_dao import TicketAttachmentDAO
from dao.ticket_dao import TicketDAO
from dao.user_dao import UserDAO


class TicketAttachmentService:

    ALLOWED_EXTENSIONS = {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "pdf",
        "txt",
        "log",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "zip"
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024

    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'tickets'))

    @staticmethod
    def _get_user(user_id):
        user = UserDAO.get_by_id(user_id)

        if not user:
            raise ValueError("User not found.")

        if not user.is_active:
            raise PermissionError(
                "User account is inactive."
            )

        return user

    @staticmethod
    def _can_access_ticket(user, ticket):
        if user.role.name == "ADMIN":
            return True

        if user.role.name == "EMPLOYEE":
            return ticket.created_by == user.id

        if user.role.name == "AGENT":

            from dao.ticket_assignment_dao import TicketAssignmentDAO

            assignments = TicketAssignmentDAO.get_by_agent(
                user.id
            )

            return any(
                assignment.ticket_id == ticket.id
                for assignment in assignments
            )

        return False

    @staticmethod
    def _validate_file(file):
        if file is None:
            raise ValueError(
                "No file was provided."
            )

        if not file.filename:
            raise ValueError(
                "Filename is required."
            )

        filename = secure_filename(
            file.filename
        )

        if not filename:
            raise ValueError(
                "Invalid filename."
            )

        extension = ""

        if "." in filename:
            extension = (
                filename.rsplit(".", 1)[1]
                .lower()
            )

        if extension not in TicketAttachmentService.ALLOWED_EXTENSIONS:
            raise ValueError(
                "File type is not allowed."
            )


        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > TicketAttachmentService.MAX_FILE_SIZE:
            raise ValueError(
                "File size cannot exceed 10 MB."
            )

        return filename, extension, file_size

    @staticmethod
    def upload_attachment(
        user_id,
        ticket_id,
        file
    ):
        user = TicketAttachmentService._get_user(
            user_id
        )

        ticket = TicketDAO.get_by_id(ticket_id)

        if not ticket:
            raise ValueError(
                "Ticket not found."
            )

        if not TicketAttachmentService._can_access_ticket(
            user,
            ticket
        ):
            raise PermissionError(
                "You are not allowed to upload "
                "attachments to this ticket."
            )

        if ticket.status == "CLOSED":
            raise ValueError(
                "Cannot attach files to a closed ticket."
            )

        (
            original_filename,
            extension,
            file_size
        ) = TicketAttachmentService._validate_file(
            file
        )

        ticket_folder = os.path.join(
            TicketAttachmentService.UPLOAD_FOLDER,
            str(ticket_id)
        )

        os.makedirs(
            ticket_folder,
            exist_ok=True
        )

        stored_filename = (
            f"{uuid.uuid4().hex}.{extension}"
        )

        file_path = os.path.join(
            ticket_folder,
            stored_filename
        )

        try:
            file.save(file_path)

        except Exception as exc:
            raise IOError(
                "Failed to save attachment."
            ) from exc

        attachment = TicketAttachment(
            ticket_id=ticket_id,
            uploaded_by=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=extension
        )

        try:
            attachment = TicketAttachmentDAO.create(
                attachment
            )

        except Exception:
            if os.path.exists(file_path):
                os.remove(file_path)

            raise

        from services.ticket_history_service import TicketHistoryService

        TicketHistoryService.create_history(
            user_id=user_id,
            ticket_id=ticket_id,
            action="ATTACHMENT_ADDED",
            description=(
                f"Attachment '{original_filename}' "
                f"was uploaded."
            )
        )

        return attachment

    @staticmethod
    def get_attachment(
        user_id,
        attachment_id
    ):
        user = TicketAttachmentService._get_user(
            user_id
        )

        attachment = TicketAttachmentDAO.get_by_id(
            attachment_id
        )

        if not attachment:
            raise ValueError(
                "Attachment not found."
            )

        ticket = TicketDAO.get_by_id(
            attachment.ticket_id
        )

        if not ticket:
            raise ValueError(
                "Ticket not found."
            )

        if not TicketAttachmentService._can_access_ticket(
            user,
            ticket
        ):
            raise PermissionError(
                "You are not allowed to access "
                "this attachment."
            )

        return attachment

    @staticmethod
    def get_ticket_attachments(
        user_id,
        ticket_id
    ):
        user = TicketAttachmentService._get_user(
            user_id
        )

        ticket = TicketDAO.get_by_id(ticket_id)

        if not ticket:
            raise ValueError(
                "Ticket not found."
            )

        if not TicketAttachmentService._can_access_ticket(
            user,
            ticket
        ):
            raise PermissionError(
                "You are not allowed to view "
                "attachments for this ticket."
            )

        return TicketAttachmentDAO.get_by_ticket(
            ticket_id
        )

    @staticmethod
    def delete_attachment(
        admin_id,
        attachment_id
    ):
        admin = TicketAttachmentService._get_user(
            admin_id
        )

        if admin.role.name != "ADMIN":
            raise PermissionError(
                "Only administrators can delete attachments."
            )

        attachment = TicketAttachmentDAO.get_by_id(
            attachment_id
        )

        if not attachment:
            raise ValueError(
                "Attachment not found."
            )

        file_path = attachment.file_path
        ticket_id = attachment.ticket_id

        TicketAttachmentDAO.delete(
            attachment
        )

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        return True