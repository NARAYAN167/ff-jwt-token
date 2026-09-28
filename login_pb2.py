"""Runtime-built protobuf descriptor for the FreeFire LoginReq message.

This avoids hand-crafting serialized descriptor bytes (which are easy to
corrupt). We construct the FileDescriptorProto at import time and register
it in a private pool, then expose the generated message class.
"""
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

_FILE = descriptor_pb2.FileDescriptorProto()
_FILE.name = "login.proto"
_FILE.package = "app.proto"
_FILE.syntax = "proto3"

msg = _FILE.message_type.add()
msg.name = "LoginReq"

def _add(name, number, ftype, label=descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL):
    f = msg.field.add()
    f.name = name
    f.number = number
    f.label = label
    f.type = ftype
    return f

# Real FreeFire protobuf tags for LoginReq:
# open_id = 22 (0x16)
# open_id_type = 23 (0x17)
# login_token = 29 (0x1d)
# orign_platform_type = 99 (0x63)
_add("open_id",              22, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
_add("open_id_type",         23, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
_add("login_token",          29, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
_add("orign_platform_type",  99, descriptor_pb2.FieldDescriptorProto.TYPE_STRING)

_pool = descriptor_pool.DescriptorPool()
_pool.Add(_FILE)
LoginReq = message_factory.GetMessageClass(
    _pool.FindMessageTypeByName("app.proto.LoginReq")
)