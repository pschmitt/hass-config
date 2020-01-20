# Usage
#
# - service: python_script.set_state
#   data_template:
#     entity_attr:
#       nuki_id: '{{ trigger.json.nukiId }}'
#     state: '{{ trigger.json.stateName }}'
#     # Attributes
#     battery_critical: '{{ trigger.json.batteryCritical }}'
#     updated_by: python_script.set_state

LOG_HANDLE = "python_script.set_state"

ATTR_ALLOW_CREATE = "allow_create"
ATTR_ENTITY_ATTR = "entity_attr"
ATTR_ENTITY_ID = "entity_id"
ATTR_STATE = "state"


def get_entity_id(data):
    entity_id = data.get(ATTR_ENTITY_ID)
    if entity_id:
        entity = hass.states.get(entity_id)
        if entity:
            return entity_id
    # Search for entity matching attribute spec
    entity_attr = data.get(ATTR_ENTITY_ATTR)
    for entity_id in hass.states.entity_ids():
        state = hass.states.get(entity_id)
        # Look for first matching entity id
        for attr_name, attr_val in entity_attr.items():
            if str(state.attributes.get(attr_name)) == str(attr_val):
                logger.debug(f"{LOG_HANDLE}: matched -> {entity_id} ({attr_name}={attr_val})")
                return entity_id


entity_id = get_entity_id(data)
logger.debug(f"{LOG_HANDLE}: Found {entity_id}")

if entity_id is None and not data.get(ATTR_ALLOW_CREATE):
    logger.error(
        f"{LOG_HANDLE}: Unable to find entity matching search criteria. You may want to add {ATTR_ALLOW_CREATE}."
    )
else:
    state = hass.states.get(entity_id)  # current state
    new_state = data.get(ATTR_STATE, state.state)  # default to current state
    new_attributes = state.attributes.copy()

    # Update attributes
    reserved_keys = [ATTR_ALLOW_CREATE, ATTR_ENTITY_ATTR, ATTR_ENTITY_ID, ATTR_STATE]
    for key, val in {x: data[x] for x in data if x not in reserved_keys}.items():
        logger.debug(f"{LOG_HANDLE}: {key}={val}")
        new_attributes[key] = val

    hass.states.set(entity_id, new_state, new_attributes)
