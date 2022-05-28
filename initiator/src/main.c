/*********************************************************************
 *        Copyright (c) 2022 Carsten Wulff Software, Norway
 * *******************************************************************
 * Created       : wulff at 2022-5-28
 * *******************************************************************
 *  The MIT License (MIT)
 *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy
 *  of this software and associated documentation files (the "Software"), to deal
 *  in the Software without restriction, including without limitation the rights
 *  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 *  copies of the Software, and to permit persons to whom the Software is
 *  furnished to do so, subject to the following conditions:
 *
 *  The above copyright notice and this permission notice shall be included in all
 *  copies or substantial portions of the Software.
 *
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 *  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 *  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 *  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 *  SOFTWARE.
 *
 ********************************************************************/


//#include <zephyr.h>
//#include <init.h>
#include <nrf.h>
#include <nrfx.h>
#include "nrf_dm.h"
#include "nrfx_config.h"
#include "nrfx_clock.h"

#include "dm.c"

static nrf_dm_config_t dm_config;


int main(void)
{

  dm_clock_init();

  debug_init();

  dm_init();

  dm_config = NRF_DM_DEFAULT_CONFIG;
  dm_config.role            = NRF_DM_ROLE_INITIATOR;
  dm_config.access_address  = 0x44ddaafa;

  while (1)
  {

    nrf_dm_status_t status = nrf_dm_configure(&dm_config);

    debug_start();
    uint32_t timeout_us = 5e6;
    status     = nrf_dm_proc_execute(timeout_us);
    debug_stop();

    if(status == NRF_DM_STATUS_SUCCESS){
      debug_pulse(10e6);
    }else{
      debug_pulse(0.5e6);
    }

  }
}
