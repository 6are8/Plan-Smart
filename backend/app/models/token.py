from app.extensions import db
from datetime import datetime


class TokenBlocklist(db.Model):
   
    __tablename__ = 'token_blocklist'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(), nullable=False, index=True)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TokenBlocklist {self.jti}>"
    
    def save(self):
        db.session.add(self)
        db.session.commit()