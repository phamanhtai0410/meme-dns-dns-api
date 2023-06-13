import json
import sys

from ens.exceptions import ENSValidationError
from eth_utils import (
    remove_0x_prefix,
    to_bytes,
    to_normalized_address,
)
from eth_utils.abi import (
    collapse_if_tuple,
)
from eth_typing import (
    ChecksumAddress,
    HexAddress,
    HexStr,
)
from hexbytes import (
    HexBytes,
)
from typing import (
    Any,
    Dict,
    cast,
)
from web3 import Web3
import idna

sys.path.append('.')
from exceptions.mns import InvalidName
from config import Config

REVERSE_REGISTRAR_DOMAIN = "addr.reverse"
EXTENDED_RESOLVER_INTERFACE_ID = HexStr("0x9061b923")  # ENSIP-10
EMPTY_ADDR_HEX = HexAddress(HexStr("0x" + "00" * 20))
EMPTY_SHA3_BYTES = HexBytes(b"\0" * 32)

web3 = Web3(Web3.HTTPProvider(Config.ETH_RPC_URI, request_kwargs={'timeout': 60}))

reverse_resolver_abi = None
with open("lib/abi/ReverseResolver.json") as reverse_resolver_file:
    reverse_resolver_abi = json.load(reverse_resolver_file)

resolver_abi = None
with open("lib/abi/Resolver.json") as resolver_file:
    resolver_abi = json.load(resolver_file)

ens_abi = None
with open("lib/abi/ENS.json") as ens_file:
    ens_abi = json.load(ens_file)

_ens_addr = ChecksumAddress(
    HexAddress(HexStr(Config.ENS_ADDRESS))
)

_reverse_resolver_contract = web3.eth.contract(
    abi=reverse_resolver_abi
)
_resolver_contract = web3.eth.contract(abi=resolver_abi)
_ens = web3.eth.contract(abi=ens_abi, address=_ens_addr)


class MNSServices:
    @classmethod
    def normalize_name(cls, name: str):
        """
        Clean the fully qualified name, as defined in ENS `EIP-137
        <https://github.com/ethereum/EIPs/blob/master/EIPS/eip-137.md#name-syntax>`_

        This does *not* enforce whether ``name`` is a label or fully qualified domain.

        :param str name: the dot-separated ENS name
        :raises InvalidName: if ``name`` has invalid syntax
        """
        if not name:
            return name
        elif isinstance(name, (bytes, bytearray)):
            name = name.decode("utf-8")

        try:
            return idna.uts46_remap(name, std3_rules=True, transitional=False)
        except idna.IDNAError as exc:
            raise InvalidName(f"{name} is an invalid name, because {exc}") from exc

    @classmethod
    def _resolver_supports_interface(cls, resolver, interface_id: HexStr) -> bool:
        if not any("supportsInterface" in repr(func) for func in resolver.all_functions()):
            return False
        return resolver.caller.supportsInterface(interface_id)

    @classmethod
    def is_empty_name(cls, name: str) -> bool:
        return name in {None, ".", ""}

    @classmethod
    def is_none_or_zero_address(cls, addr) -> bool:
        return not addr or addr == EMPTY_ADDR_HEX

    @classmethod
    def ens_encode_name(cls, name: str) -> bytes:
        """
        Encode a name according to DNS standards specified in section 3.1
        of RFC1035 with the following validations:

            - There is no limit on the total length of the encoded name
            and the limit on labels is the ENS standard of 255.

            - Return a single 0-octet, b'\x00', if empty name.
        """
        if cls.is_empty_name(name):
            return b"\x00"

        normalized_name = cls.normalize_name(name)

        labels = normalized_name.split(".")
        labels_as_bytes = [to_bytes(text=label) for label in labels]

        # raises if len(label) > 255:
        for index, label in enumerate(labels):
            if len(label) > 255:
                raise ENSValidationError(
                    f"Label at position {index} too long after encoding."
                )

        # concat label size in bytes to each label:
        dns_prepped_labels = [to_bytes(len(label)) + label for label in labels_as_bytes]

        # return the joined prepped labels in order and append the zero byte at the end:
        return b"".join(dns_prepped_labels) + b"\x00"

    @classmethod
    def label_to_hash(cls, label: str) -> HexBytes:
        label = cls.normalize_name(label)
        if "." in label:
            raise ValueError(f"Cannot generate hash for label {label!r} with a '.'")
        return Web3().keccak(text=label)

    @classmethod
    def normal_name_to_hash(cls, name: str):
        node = EMPTY_SHA3_BYTES
        if name:
            labels = name.split(".")
            for label in reversed(labels):
                labelhash = cls.label_to_hash(label)
                assert isinstance(labelhash, bytes)
                assert isinstance(node, bytes)
                node = Web3().keccak(node + labelhash)
        return node

    @classmethod
    def _type_aware_resolver(
            cls,
            address: ChecksumAddress,
            func: str,
    ):
        return (
            _reverse_resolver_contract(address=address)
            if func == "name"
            else _resolver_contract(address=address)
        )

    @classmethod
    def parent(cls, name: str) -> str:
        """
        Part of ENSIP-10. Returns the parent of a given ENS name,
        or the empty string if the ENS name does not have a parent.

        e.g.
        - parent('1.foo.bar.eth') = 'foo.bar.eth'
        - parent('foo.bar.eth') = 'bar.eth'
        - parent('foo.eth') = 'eth'
        - parent('eth') is defined as the empty string ''

        :param name: an ENS name
        :return: the parent for the provided ENS name
        :rtype: str
        """
        if not name:
            return ""

        labels = name.split(".")
        return "" if len(labels) == 1 else ".".join(labels[1:])

    @classmethod
    def _get_resolver(
            cls,
            normal_name: str,
            fn_name: str = "addr",
    ):
        current_name = normal_name

        # look for a resolver, starting at the full name and taking the parent
        # each time that no resolver is found
        while True:
            if cls.is_empty_name(current_name):
                # if no resolver found across all iterations, current_name
                # will eventually be the empty string '' which returns here
                return None, current_name

            resolver_addr = _ens.caller.resolver(cls.normal_name_to_hash(current_name))
            print(f'resolver_address {resolver_addr}')
            if not cls.is_none_or_zero_address(resolver_addr):
                # if resolver found, return it
                resolver = cast(
                    "Contract", cls._type_aware_resolver(resolver_addr, fn_name)
                )
                return resolver, current_name

            # set current_name to parent and try again
            current_name = cls.parent(current_name)

    @classmethod
    def namehash(cls, name: str) -> HexBytes:
        return cls.raw_name_to_hash(name)

    @classmethod
    def raw_name_to_hash(cls, name: str) -> HexBytes:
        """
        Generate the namehash. This is also known as the ``node`` in ENS contracts.

        In normal operation, generating the namehash is handled
        behind the scenes. For advanced usage, it is a helpful utility.

        This normalizes the name with `nameprep
        <https://github.com/ethereum/EIPs/blob/master/EIPS/eip-137.md#name-syntax>`_
        before hashing.

        :param str name: ENS name to hash
        :return: the namehash
        :rtype: bytes
        :raises InvalidName: if ``name`` has invalid syntax
        """
        normalized_name = cls.normalize_name(name)
        return cls.normal_name_to_hash(normalized_name)

    # borrowed from similar method at `web3._utils.abi` due to circular dependency
    @classmethod
    def get_abi_output_types(cls, abi):
        return (
            []
            if abi["type"] == "fallback"
            else [collapse_if_tuple(cast(Dict[str, Any], arg)) for arg in abi["outputs"]]
        )

    @classmethod
    def _decode_ensip10_resolve_data(
            cls,
            contract_call_result: bytes,
            extended_resolver,
            fn_name: str,
    ):
        func = extended_resolver.get_function_by_name(fn_name)
        output_types = cls.get_abi_output_types(func.abi)
        decoded = web3.codec.decode(output_types, contract_call_result)

        # if decoding a single value, return that value - else, return the tuple
        return decoded[0] if len(decoded) == 1 else decoded

    @classmethod
    def _resolve(
            cls,
            name: str, fn_name: str = "addr"
    ):
        normal_name = cls.normalize_name(name)

        print(f"normal name {normal_name}")

        resolver, current_name = cls._get_resolver(normal_name, fn_name)
        # print(f'_resolver {_resolver}')
        if not resolver:
            return None

        node = cls.namehash(normal_name)

        # handle extended resolver case
        if cls._resolver_supports_interface(resolver, EXTENDED_RESOLVER_INTERFACE_ID):
            contract_func_with_args = (fn_name, [node])

            calldata = resolver.encodeABI(*contract_func_with_args)
            contract_call_result = resolver.caller.resolve(
                cls.ens_encode_name(normal_name), calldata
            )
            result = cls._decode_ensip10_resolve_data(
                contract_call_result, resolver, fn_name
            )
            return web3.to_checksum_address(result) if web3.is_address(result) else result
        elif normal_name == current_name:
            lookup_function = getattr(resolver.functions, fn_name)
            result = lookup_function(node).call()
            if cls.is_none_or_zero_address(result):
                return None
            return web3.to_checksum_address(result) if web3.is_address(result) else result
        return None

    @classmethod
    def address_to_reverse_domain(cls, address) -> str:
        lower_unprefixed_address = remove_0x_prefix(HexStr(to_normalized_address(address)))
        return lower_unprefixed_address + "." + REVERSE_REGISTRAR_DOMAIN

    @classmethod
    def addressfunc(cls, name: str):
        """
        Look up the Ethereum address that `name` currently points to.

        :param str name: an ENS name to look up
        :raises InvalidName: if `name` has invalid syntax
        """
        return cast(ChecksumAddress, cls._resolve(name, "addr"))

    @classmethod
    def name(cls, address):
        _address = web3.to_checksum_address(address)

        reversed_domain = cls.address_to_reverse_domain(_address)
        name = cls._resolve(name=reversed_domain, fn_name="name")

        # To be absolutely certain of the name, via reverse resolution,
        # the address must match in the forward resolution
        return name if web3.to_checksum_address(_address) == cls.addressfunc(name) else None

    @classmethod
    def address(cls, name: str):
        """
        Look up the Ethereum address that `name` currently points to.

        :param str name: an ENS name to look up
        :raises InvalidName: if `name` has invalid syntax
        """
        return cast(ChecksumAddress, cls._resolve(name, "addr"))
