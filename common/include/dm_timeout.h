/*********************************************************************
 *        Copyright (c) 2022 Carsten Wulff Software, Norway
 ********************************************************************/

#ifndef DM_TIMEOUT_H
#define DM_TIMEOUT_H

/* Initiator: active procedure (~21 ms measured) + overhead. */
#ifndef DM_INITIATOR_TIMEOUT_US
#define DM_INITIATOR_TIMEOUT_US 50000
#endif

/* Reflector: wait for initiator sync; Nordic recommends larger than initiator. */
#ifndef DM_REFLECTOR_TIMEOUT_US
#define DM_REFLECTOR_TIMEOUT_US 500000
#endif

#endif
