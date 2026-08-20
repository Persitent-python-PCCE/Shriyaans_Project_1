from config.database import db
from models.ticket_attachment import TicketAttachment


class TicketAttachmentDAO:

    @staticmethod
    def create(attachment):
        db.session.add(attachment)
        db.session.commit()
        return attachment

    @staticmethod
    def get_by_id(attachment_id):
        return db.session.get(
            TicketAttachment,
            attachment_id
        )

    @staticmethod
    def get_by_ticket(ticket_id):
        return TicketAttachment.query.filter_by(
            ticket_id=ticket_id
        ).all()

    @staticmethod
    def delete(attachment):
        db.session.delete(attachment)
        db.session.commit()