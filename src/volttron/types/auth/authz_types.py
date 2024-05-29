from typing import Any

from attrs import validators, define, field, fields
from cattrs import Converter

vipid_dot_rpc_method = str
RPC_CAPABILITIES = "rpc_capabilities"
PUBSUB_CAPABILITIES = "pubsub_capabilities"
ROLES = "roles"

@define
class RPCCapability:
    resource = field(type=vipid_dot_rpc_method)
    param_restrictions = field(type=dict, default=dict())

    def add_param_restrictions(self, param: str, value: Any):
        self.param_restrictions[param] = value


@define
class RPCCapabilities:
    rpc_capabilities = field(type=list[RPCCapability], default=[])

    def add_rpc_capability(self, c: RPCCapability):
        if c.resource not in self.rpc_capabilities:
            self.rpc_capabilities.append(c)

    def remove_rpc_capability(self, c: RPCCapability):
        try:
            self.rpc_capabilities.remove(c)
        except ValueError:
            pass

    def __len__(self):
        return len(self.rpc_capabilities)


def unstructure_rpc_capabilities(instance: RPCCapabilities):
    """
    Convert from:

        RPCCapabilities(
        rpc_capabilities=[RPCCapability(resource='id.rpc1', param_restrictions={}),
                          RPCCapability(resource='id2.rpc2', param_restrictions={'id': 'id2', 'p2': 'v2'})])

    TO:
        ['id.rpc1', {'id2.rpc2': {'id': 'id2', 'p2': 'v2'}}]
        i.e. instead of the default unstructure/asdict behavior - list of {resource:value, param_restrictions:value}
        generate single List with just resource str if param_restrictions is None or dict(resource, param_restriction)

    """
    rpc_capabilities_list = []
    for c in instance.rpc_capabilities:
        if c.param_restrictions:
            rpc_capabilities_list.append({c.resource: c.param_restrictions})
        else:
            rpc_capabilities_list.append(c.resource)
    return rpc_capabilities_list


@define
class PubsubCapability:
    topic_pattern = field(type=str)
    topic_access = field(validator=validators.in_(["publish", "subscribe", "pubsub"]))


@define
class PubsubCapabilities:
    # todo check for duplicates
    pubsub_capabilities = field(type=list[PubsubCapability], default=[])

    def add_pubsub_capability(self, c: PubsubCapability):
        if c not in self.pubsub_capabilities:
            self.pubsub_capabilities.append(c)

    def remove_pubsub_capability(self, c: PubsubCapability):
        try:
            self.pubsub_capabilities.remove(c)
        except ValueError:
            pass

    def __len__(self):
        return len(self.pubsub_capabilities)


def unstructure_pubsub_capabilities(instance: PubsubCapabilities):
    """
    Convert from:
        PubsubCapabilities(
        pubsub_capabilities=[PubsubCapability(topic_pattern='device/*', topic_access='pubsub'),
                             PubsubCapability(topic_pattern='*', topic_access='pubsub')])
    TO:
        {'device/*': 'pubsub', '*': 'pubsub'}
        i.e. instead of the default - list of dict with topic_pattern:<value>, topic_access: <value>
             generate single dict with key as topic_pattern and values topic_access
    """
    pubsub_capabilities_dict = dict()
    for c in instance.pubsub_capabilities:
        pubsub_capabilities_dict[c.topic_pattern] = c.topic_access
    return pubsub_capabilities_dict


@define
class Role:
    name = field(type=str)
    rpc_capabilities = field(type=RPCCapabilities, default=None)
    pubsub_capabilities = field(type=PubsubCapabilities, default=None)

    def add_rpc_capability(self, c: RPCCapability):
        self.rpc_capabilities.add_rpc_capability(c)

    def remove_rpc_capability(self, c: RPCCapability):
        self.rpc_capabilities.remove_rpc_capability(c)


@define
class Roles:
    roles = field(type=list[Role], default=[])

    def __len__(self):
        return len(self.roles)


def unstructure_roles(instance: Roles):
    """
    Convert from:
        Roles(roles=[
          Role(name='admin',
               rpc_capabilities=RPCCapabilities(rpc_capabilities=[
                                 RPCCapability(resource='id.rpc1', param_restrictions={}),
                                 RPCCapability(resource='id2.rpc2', param_restrictions={'id': 'id2', 'p2': 'v2'})]),
               pubsub_capabilities=None),
          Role(name='new_role',
               rpc_capabilities=None,
               pubsub_capabilities=PubsubCapabilities(pubsub_capabilities=[
                                     PubsubCapability(topic_pattern='device/*', topic_access='pubsub'),
                                     PubsubCapability(topic_pattern='*', topic_access='pubsub')]))
          ])

    TO:
        {'admin': {'rpc_capabilities': ['id.rpc1', {'id2.rpc2': {'id': 'id2', 'p2': 'v2'}}]},
         'new_role': {'pubsub_capabilities': {'device/*': 'pubsub', '*': 'pubsub'}}}

        i.e. instead of list of dict with name:<value>, rpc_capabilities: <list>, pubsub_capabilities: <list>
             generate dict with key as role name and values as rpc and pubsub capabilities and skip none values
    """
    _roles_dict = dict()
    for _r in instance.roles:
        _roles_dict[_r.name] = dict()
        if _r.rpc_capabilities:
            _roles_dict[_r.name][RPC_CAPABILITIES] = authz_converter.unstructure(_r.rpc_capabilities)
        if _r.pubsub_capabilities:
            _roles_dict[_r.name][PUBSUB_CAPABILITIES] = authz_converter.unstructure(_r.pubsub_capabilities)
    return _roles_dict


role_name = str
Identity = str


@define
class UserGroup:
    name = field(type=str)
    identities = field(type=set[Identity], default=set())
    roles = field(type=set[role_name], default=set())
    rpc_capabilities = field(type=RPCCapabilities, default=None)
    pubsub_capabilities = field(type=PubsubCapabilities, default=None)


@define
class UserGroups:
    user_groups = field(type=list[UserGroup], default=[])

    def __len__(self):
        return len(self.user_groups)


def unstructure_user_groups(instance: UserGroups):
    """
    Convert
      UserGroups(user_groups=[
        UserGroup(name='admin_users',
                  users=['volttron.ctl', 'config.store'],
                  roles=['admin'],
                  rpc_capabilities=None,
                  pubsub_capabilities=PubsubCapabilities(pubsub_capabilities=[
                    PubsubCapability(topic_pattern='device/*', topic_access='pubsub'),
                    PubsubCapability(topic_pattern='*', topic_access='pubsub')])
                  )
        ])

    TO:
    {'admin_users':
        {'users': ['volttron.ctl', 'config.store'],
         'roles': ['admin'],
         'pubsub_capabilities': {'device/*': 'pubsub', '*': 'pubsub'}
         }
    }
    i.e. instead of list of dict with
                  name:<value>, users:<list>, roles:<list>, rpc_capabilities: <list>, pubsub_capabilities: <list>
    generate dict with key as group name and values as users, roles, rpc, pubsub capabilities and skipping none
    """
    _groups_dict = dict()
    for _g in instance.user_groups:
        _groups_dict[_g.name] = {'identities': _g.identities}
        if _g.roles:
            _groups_dict[_g.name]['roles'] = authz_converter.unstructure(_g.roles)
        if _g.rpc_capabilities:
            _groups_dict[_g.name][RPC_CAPABILITIES] = authz_converter.unstructure(_g.rpc_capabilities)
        if _g.pubsub_capabilities:
            _groups_dict[_g.name][PUBSUB_CAPABILITIES] = authz_converter.unstructure(_g.pubsub_capabilities)

    return _groups_dict


@define
class User:
    identity = field(type=Identity)
    protected_rpcs = field(type=set[vipid_dot_rpc_method], default=None)
    roles = field(type=set[role_name], default=None)
    rpc_capabilities = field(type=RPCCapabilities, default=None)
    pubsub_capabilities = field(type=PubsubCapabilities, default=None)
    comments = field(type=str, default=None)
    domain = field(type=str, default=None)
    address = field(type=str, default=None)


@define
class Users:
    users = field(type=list[User])

    def __len__(self):
        return len(self.users)


def unstructure_users(instance: Users):
    _users_dict = dict()
    # make a dict with key as user name and value as dict of all other attributes. In the inner dict, values are
    # converted from attrs objects to primitives based on its own custom unstructure methods
    for _user in instance.users:
        _users_dict[_user.identity] = dict()
        for attribute in fields(_user.__class__):
            if attribute.name != "identity" and _user.__getattribute__(attribute.name):
                _users_dict[_user.identity][attribute.name] = (
                    authz_converter.unstructure(_user.__getattribute__(attribute.name)))
    return _users_dict


@define
class VolttronAuthzMap:
    protected_topics: field(type=set[str], default=None)
    roles: field(type=Roles, default=None)
    user_groups: field(type=UserGroups, default=None)
    users: field(type=Users, default=None)
    compact_dict: field(type=dict, init=False, default=None)

    def __attrs_post_init__(self):
        self.compact_dict = dict()

    @classmethod
    def create_rpc_capabilities_obj(cls, rpc_cap_list: list = None) -> RPCCapabilities:
        if rpc_cap_list is None:
            rpc_cap_list = list()
        obj_list = RPCCapabilities([])  # I don't get a new instance of list in obj if I don't pass []  ?!
        for rpc_cap in rpc_cap_list:
            if isinstance(rpc_cap, str):
                obj_list.add_rpc_capability(RPCCapability(rpc_cap))
            elif isinstance(rpc_cap, dict):
                vip_id_rpc_method = list(rpc_cap.keys())[0]
                param_restrict = rpc_cap[vip_id_rpc_method]
                obj_list.add_rpc_capability(RPCCapability(vip_id_rpc_method, param_restrict))
        return obj_list

    @classmethod
    def create_pubsub_capabilities_obj(cls, pubsub_cap_dict: dict = None) -> PubsubCapabilities:
        if pubsub_cap_dict is None:
            pubsub_cap_dict = dict()
        obj_list = PubsubCapabilities([])  # I don't get a new instance of list in obj if I don't pass []  ?!
        for topic_pattern, access in pubsub_cap_dict.items():
            obj_list.add_pubsub_capability(PubsubCapability(topic_pattern, access))
        return obj_list

    @classmethod
    def from_unstructured_dict(cls, authz_compact_dict: dict):
        protected_topics = authz_compact_dict.get("protected_topics")

        # Build Roles
        _roles = list()
        for name, value in authz_compact_dict.get(ROLES, dict()).items():
            rpc_obj_list = VolttronAuthzMap.create_rpc_capabilities_obj(value.get(RPC_CAPABILITIES))
            pubsub_obj_list = VolttronAuthzMap.create_pubsub_capabilities_obj(value.get(PUBSUB_CAPABILITIES))

            r_obj = Role(name, rpc_capabilities=rpc_obj_list, pubsub_capabilities=pubsub_obj_list)
            _roles.append(r_obj)

        # Build user groups
        groups = list()
        for group_name, value in authz_compact_dict.get("user_groups", dict()).items():
            vip_ids = value.get("identities", list())
            role_names = value.get(ROLES, list())
            rpc_obj_list = VolttronAuthzMap.create_rpc_capabilities_obj(value.get(RPC_CAPABILITIES))
            pubsub_obj_list = VolttronAuthzMap.create_pubsub_capabilities_obj(value.get(PUBSUB_CAPABILITIES))
            groups.append(UserGroup(name=group_name, identities=vip_ids, roles=role_names,
                                    rpc_capabilities=rpc_obj_list, pubsub_capabilities=pubsub_obj_list))

        # Build users
        users = list()
        for identity, value in authz_compact_dict.get("users", dict()).items():
            protected_rpcs = value.get("protected_rpcs", list())
            role_names = value.get(ROLES, list())
            rpc_obj_list = VolttronAuthzMap.create_rpc_capabilities_obj(value.get(RPC_CAPABILITIES))
            pubsub_obj_list = VolttronAuthzMap.create_pubsub_capabilities_obj(value.get(PUBSUB_CAPABILITIES))
            comments = value.get("comments")
            domain = value.get("domain")
            address = value.get("address")
            users.append(User(identity=identity,
                              protected_rpcs=protected_rpcs,
                              roles=role_names,
                              rpc_capabilities=rpc_obj_list,
                              pubsub_capabilities=pubsub_obj_list,
                              comments=comments,
                              domain=domain,
                              address=address))

        authz_roles = Roles(_roles)
        authz_user_groups = UserGroups(groups)
        authz_users = Users(users)
        instance = cls(protected_topics=protected_topics,
                       roles=authz_roles,
                       user_groups=authz_user_groups,
                       users=authz_users)
        # print(json.dumps(authz.authz_converter.unstructure(instance), indent=4))
        instance.compact_dict = authz_compact_dict
        return instance

    def create_merge_role(self, *, name: str, rpc_capabilities: RPCCapabilities = None,
                          pubsub_capabilities: PubsubCapabilities = None) -> bool:
        if not rpc_capabilities and not pubsub_capabilities:
            raise ValueError(f"Role {name} should have non empty capabilities - rpc capabilities, "
                             "pubsub capabilities or both")
        if not self.compact_dict.get(ROLES):
            self.compact_dict[ROLES] = dict()
        if name not in self.compact_dict.get(ROLES):
            self.compact_dict.get(ROLES)[name] = dict()

        role_dict = self.compact_dict.get(ROLES).get(name)
        if rpc_capabilities:
            current_rpc_caps = role_dict.get(RPC_CAPABILITIES, [])
            s = set(current_rpc_caps)
            s.update(authz_converter.unstructure(rpc_capabilities))
            role_dict[RPC_CAPABILITIES] = list(s)
        if pubsub_capabilities:
            current_pubsub_caps = role_dict.get(PUBSUB_CAPABILITIES, dict())
            current_pubsub_caps.update(authz_converter.unstructure(pubsub_capabilities))
            role_dict[PUBSUB_CAPABILITIES] = current_pubsub_caps
        return True

    def create_or_merge_user_group(self, *, name: str, identities: set[Identity], roles: set[role_name],
                                   rpc_capabilities: RPCCapabilities, pubsub_capabilities: PubsubCapabilities,
                                   **kwargs) -> bool:
        if not identities:
            raise ValueError("Empty user group")
        if not roles and not rpc_capabilities and not pubsub_capabilities:
            raise ValueError(f"User group {name} should have non empty capabilities. Please pass non empty values "
                             "for at least one of the three parameters - roles, rpc_capabilities, pubsub_capabilities")

        if not self.compact_dict.get("user_groups"):
            self.compact_dict["user_groups"] = dict()
        if name not in self.compact_dict.get("user_groups"):
            self.compact_dict.get("user_groups")[name] = dict()

        group_dict = self.compact_dict.get("user_groups").get(name)

        current_ids_set = set(group_dict.get("identities", list()))
        current_ids_set.update(identities)
        group_dict["identities"] = list(current_ids_set)

        if roles:
            current_roles_set = set(group_dict.get(ROLES, list()))
            current_roles_set.update(roles)
            group_dict[ROLES] = list(current_roles_set)

        if rpc_capabilities:
            current_rpc_caps = group_dict.get(RPC_CAPABILITIES, [])
            s = set(current_rpc_caps)
            s.update(authz_converter.unstructure(rpc_capabilities))
            group_dict[RPC_CAPABILITIES] = list(s)

        if pubsub_capabilities:
            current_pubsub_caps = group_dict.get(PUBSUB_CAPABILITIES, dict())
            current_pubsub_caps.update(authz_converter.unstructure(pubsub_capabilities))
            group_dict[PUBSUB_CAPABILITIES] = current_pubsub_caps
        return True
    
    def create_or_merge_user_authz(self, *, identity: str, protected_rpcs: set[vipid_dot_rpc_method],
                                   roles: set[role_name], rpc_capabilities: RPCCapabilities,
                                   pubsub_capabilities: PubsubCapabilities, comments: str | None,
                                   domain: str | None, address: str | None, **kwargs) -> bool:

        if not identity:
            raise ValueError("User identity is mandatory")

        if not self.compact_dict.get("users"):
            self.compact_dict["users"] = dict()
        if identity not in self.compact_dict.get("users"):
            self.compact_dict.get("users")[identity] = dict()

        user_dict = self.compact_dict.get("users").get(identity)

        if protected_rpcs:
            current_rpc_set = set(user_dict.get("protected_rpcs", list()))
            current_rpc_set.update(protected_rpcs)
            user_dict["protected_rpcs"] = list(current_rpc_set)

        if roles:
            current_roles_set = set(user_dict.get(ROLES, list()))
            current_roles_set.update(roles)
            user_dict[ROLES] = list(current_roles_set)

        if rpc_capabilities:
            current_rpc_caps = user_dict.get(RPC_CAPABILITIES, [])
            s = set(current_rpc_caps)
            s.update(authz_converter.unstructure(rpc_capabilities))
            user_dict[RPC_CAPABILITIES] = list(s)

        if pubsub_capabilities:
            current_pubsub_caps = user_dict.get(PUBSUB_CAPABILITIES, dict())
            current_pubsub_caps.update(authz_converter.unstructure(pubsub_capabilities))
            user_dict[PUBSUB_CAPABILITIES] = current_pubsub_caps
        if comments:
            user_dict["comments"] = comments

        if domain:
            user_dict["domain"] = domain

        if address:
            user_dict["address"] = address

        return True

    def create_protected_topic(self, *, topic_name_pattern: str) -> bool:
        _topics = self.compact_dict.get("protected_topics", [])
        if topic_name_pattern in _topics:
            return False
        else:
            _topics.append(topic_name_pattern)
            self.compact_dict["protected_topics"] = _topics
            return True

    def remove_protected_topic(self, *, topic_name_pattern: str) -> bool:
        if not self.compact_dict.get("protected_topics"):
            return False
        try:
            self.compact_dict.get("protected_topics").remove(topic_name_pattern)
            return True
        except KeyError:
            return False

    def remove_user(self, identity: Identity):
        if not self.compact_dict.get("users") or identity not in self.compact_dict.get("users"):
            return False
        else:
            del self.compact_dict.get("users")[identity]
            return True

    def remove_user_group(self, name: str):
        if not self.compact_dict.get("user_groups") or name not in self.compact_dict.get("user_groups"):
            return False
        else:
            del self.compact_dict.get("user_groups")[name]
            return True

    def remove_role(self, name: str):
        if not self.compact_dict.get(ROLES) or name not in self.compact_dict.get(ROLES):
            return False
        else:
            del self.compact_dict.get(ROLES)[name]
            return True


def unstructure_authz_map(instance: VolttronAuthzMap):
    authz_map_dict = dict()
    if instance.protected_topics:
        authz_map_dict["protected_topics"] = instance.protected_topics
    if instance.roles:
        authz_map_dict[ROLES] = authz_converter.unstructure(instance.roles)
    if instance.user_groups:
        authz_map_dict["user_groups"] = authz_converter.unstructure(instance.user_groups)
    if instance.users:
        authz_map_dict["users"] = authz_converter.unstructure(instance.users)
    return authz_map_dict


authz_converter = Converter()
authz_converter.register_unstructure_hook(RPCCapabilities, unstructure_rpc_capabilities)
authz_converter.register_unstructure_hook(PubsubCapabilities, unstructure_pubsub_capabilities)
authz_converter.register_unstructure_hook(Roles, unstructure_roles)
authz_converter.register_unstructure_hook(UserGroups, unstructure_user_groups)
authz_converter.register_unstructure_hook(Users, unstructure_users)
authz_converter.register_unstructure_hook(VolttronAuthzMap, unstructure_authz_map)

###############
# test
###############
if __name__ == "__main__":
    r1 = RPCCapability("id.rpc1")
    r2 = RPCCapability("id2.rpc2", {"id": "id2", "p2": "v2"})
    rpc_list = RPCCapabilities([r1, r2])
    print(rpc_list)
    rpc_dict = authz_converter.unstructure(rpc_list)
    print(rpc_dict)
    pubsub_list = PubsubCapabilities([PubsubCapability(topic_pattern="device/*", topic_access="pubsub"),
                                      PubsubCapability(topic_pattern="*", topic_access="pubsub")])
    print(pubsub_list)
    pubsub_dict = authz_converter.unstructure(pubsub_list)
    print(pubsub_dict)

    r = Role("admin", rpc_list, pubsub_list)
    print(r)
    r_dict = authz_converter.unstructure(r)
    print(r_dict)
    roles = Roles([Role("admin", rpc_list), Role("new_role", pubsub_capabilities=pubsub_list)])
    print(roles)
    roles_dict = authz_converter.unstructure(roles)
    print(roles_dict)

    g = UserGroups([UserGroup("admin_users", {"volttron.ctl", "config.store"}, roles={"admin"},
                              pubsub_capabilities=pubsub_list)])
    print(g)
    g_dict = authz_converter.unstructure(g)
    print(g_dict)

    u = Users([User("volttron.ctl", roles={"admin"}), User("hist1", rpc_capabilities=rpc_list)])
    print(u)
    u_dict = authz_converter.unstructure(u)
    print(u_dict)
