from marshmallow import Schema, RAISE, fields


class MarketplaceNFTDetailRequestSchema(Schema):
    class Meta:
        unknown = RAISE

    token_id = fields.Str(required=True)
