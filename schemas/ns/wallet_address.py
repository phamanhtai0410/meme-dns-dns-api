from marshmallow import Schema, RAISE, fields


class NameServiceWalletAddressRequestSchema(Schema):
    class Meta:
        unknown = RAISE

    web3_name = fields.Str(required=True)
