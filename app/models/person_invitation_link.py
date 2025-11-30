"""PersonInvitationLink model for person-specific invitation short links."""
import secrets
from datetime import datetime
from app import db


class PersonInvitationLink(db.Model):
    """Stores person-specific short tokens for invitation links.

    While EventInvitation is per-household, this model allows each person
    in a household to have their own unique short link for personalization.
    """

    __tablename__ = "person_invitation_links"

    id = db.Column(db.Integer, primary_key=True)
    invitation_id = db.Column(
        db.Integer,
        db.ForeignKey("event_invitations.id", ondelete="CASCADE"),
        nullable=False
    )
    person_id = db.Column(
        db.Integer,
        db.ForeignKey("persons.id", ondelete="CASCADE"),
        nullable=False
    )
    short_token = db.Column(db.String(16), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    invitation = db.relationship("EventInvitation", back_populates="person_links")
    person = db.relationship("Person", back_populates="invitation_links")

    # Constraints - one link per person per invitation
    __table_args__ = (
        db.UniqueConstraint(
            "invitation_id", "person_id",
            name="uq_person_invitation_link"
        ),
    )

    def __repr__(self):
        return f"<PersonInvitationLink person_id={self.person_id} token={self.short_token[:6]}...>"

    @staticmethod
    def generate_short_token():
        """Generate a unique short token.

        Returns:
            A URL-safe token (10 characters, ~60 bits of entropy)
        """
        max_attempts = 5
        for _ in range(max_attempts):
            token = secrets.token_urlsafe(8)[:10]
            existing = PersonInvitationLink.query.filter_by(short_token=token).first()
            if not existing:
                return token

        # Fallback with timestamp to ensure uniqueness
        return f"{secrets.token_urlsafe(6)}_{int(datetime.utcnow().timestamp()) % 10000}"

    @classmethod
    def get_or_create(cls, invitation, person):
        """Get existing link or create a new one for a person.

        Args:
            invitation: EventInvitation object
            person: Person object

        Returns:
            PersonInvitationLink object
        """
        link = cls.query.filter_by(
            invitation_id=invitation.id,
            person_id=person.id
        ).first()

        if not link:
            link = cls(
                invitation_id=invitation.id,
                person_id=person.id,
                short_token=cls.generate_short_token()
            )
            db.session.add(link)
            db.session.commit()

        return link

    @classmethod
    def get_by_short_token(cls, short_token):
        """Find a person invitation link by its short token.

        Args:
            short_token: The short token to look up

        Returns:
            PersonInvitationLink object or None if not found
        """
        if not short_token:
            return None
        return cls.query.filter_by(short_token=short_token).first()

    def get_short_url(self, _external=True):
        """Get the short URL for this person-specific invitation link.

        Args:
            _external: Whether to generate an absolute URL

        Returns:
            URL string (e.g., https://domain.com/i/abc123xyz)
        """
        from flask import url_for
        return url_for(
            "public.person_short_redirect",
            short_token=self.short_token,
            _external=_external
        )

