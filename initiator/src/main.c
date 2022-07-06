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
#include "nrfx_uarte.h"
#include <stdint.h>
#include <stdbool.h>


#ifndef TXD_PIN
#define TXD_PIN 6
#endif

#ifndef RXD_PIN
#define RXD_PIN 8
#endif


// Common functions, probably need to copy this file if you're on windows
#include "dm.c"


//------------------------------------------------------------------
// Setup UARTE to PC
//------------------------------------------------------------------
static nrfx_uarte_t instance = NRFX_UARTE_INSTANCE(0);

void uart_init(void){
    nrfx_uarte_config_t config = NRFX_UARTE_DEFAULT_CONFIG(TXD_PIN, RXD_PIN);
    config.baudrate            = NRF_UARTE_BAUDRATE_115200;
    nrfx_uarte_init(&instance, &config, NULL);
}

void uart_uninit(void){
    nrfx_uarte_uninit(&instance);
}

void uart_put_string(const char * string)
{
  while (*string != '\0')
  {
    uart_put_char(*string++);
  }
}

int uart_cbprint(int ch, void * ctx){
  nrfx_uarte_tx(&instance, &ch, 1);
}

void uart_put_char(uint8_t ch)
{
  nrfx_uarte_tx(&instance, &ch, 1);
}

bool uart_chars_available(void)
{
  return nrfx_uarte_rx_ready(&instance);
}

void uart_get_char(uint8_t * p_ch)
{
  nrfx_uarte_errorsrc_get(&instance);
  nrfx_uarte_rx(&instance, p_ch, 1);
}

void dist_to_json(char *str, float f){

  int d = ((int)1000*f);
  cbprintf(&uart_cbprint, 0, "\"%s\" : %d",str, d);
}

void int_to_json(char *str, int d){
  cbprintf(&uart_cbprint, 0, "\"%s\" : %d",str, d);
}

void tones_to_json(char * str, float *array,uint32_t length){

  uart_put_string("\"");
  uart_put_string(str);
  uart_put_string("\":[");
  for (uint32_t i = 0; i < length; i++)
  {
    //- Assume 10-bit ADC, and scale resolution to 15-bit, should be more than enough precision
    int f = ((int)32*array[i]);
    cbprintf(&uart_cbprint, 0, "%d", f);

    if ((i + 1) < length)
    {
      uart_put_string(",");
    }
  }
  uart_put_string("]");
}

void sinr_to_json(char * str, nrf_dm_sinr_indicator_t *array,uint32_t length){

  uart_put_string("\"");
  uart_put_string(str);
  uart_put_string("\":[");
  for (uint32_t i = 0; i < length; i++)
  {

    cbprintf(&uart_cbprint, 0, "%d", ((int)array[i]));

    if ((i + 1) < length)
    {
      uart_put_string(",");
    }
  }
  uart_put_string("]");
}

void nrf_dm_report_to_json(nrf_dm_report_t *dm_report,float distance){
  uart_put_string("{");

  //- Print tones

  tones_to_json("i_local",&dm_report->iq_tones->i_local[0],80); uart_put_string(",");
  tones_to_json("q_local",&dm_report->iq_tones->q_local[0],80); uart_put_string(",");
  tones_to_json("i_remote",&dm_report->iq_tones->i_remote[0],80); uart_put_string(",");
  tones_to_json("q_remote",&dm_report->iq_tones->q_remote[0],80); uart_put_string(",");


  //- Print tone_sinr
  sinr_to_json("sinr_local",&dm_report->tone_sinr_indicators.sinr_indicator_local[0],80); uart_put_string(",");
  sinr_to_json("sinr_remote",&dm_report->tone_sinr_indicators.sinr_indicator_remote[0],80); uart_put_string(",");

  //- Print ranging mode
  //- Print distance
  dist_to_json("ifft[mm]",dm_report->distance_estimates.mcpd.ifft);uart_put_char(',');
  dist_to_json("phase_slope[mm]",dm_report->distance_estimates.mcpd.phase_slope);uart_put_char(',');
  dist_to_json("rssi_openspace[mm]",dm_report->distance_estimates.mcpd.rssi_openspace);uart_put_char(',');
  dist_to_json("best[mm]",dm_report->distance_estimates.mcpd.best);uart_put_char(',');
  dist_to_json("highpres[mm]",((int)1000*distance));uart_put_char(',');

  //- Status params
  int_to_json("link_loss[dB]",dm_report->link_loss); uart_put_char(',');
  int_to_json("rssi_local[dB]",dm_report->rssi_local); uart_put_char(',');
  int_to_json("rssi_remote[dB]",dm_report->rssi_remote); uart_put_char(',');
  int_to_json("txpwr_local[dB]",dm_report->txpwr_local); uart_put_char(',');
  int_to_json("txpwr_remote[dB]",dm_report->txpwr_remote); uart_put_char(',');
  int_to_json("quality",dm_report->quality);
  uart_put_string("}\n\r");
}

//------------------------------------------------------------------
// Main loop
//------------------------------------------------------------------

static nrf_dm_config_t dm_config;
static nrf_dm_report_t dm_report;

int main(void)
{

  //- Functions in dm.c to init stuff
  dm_clock_init();
  debug_init();
  dm_init();

  dm_config = NRF_DM_DEFAULT_CONFIG;
  dm_config.role            = NRF_DM_ROLE_INITIATOR;
  dm_config.access_address  = 0x44ddaafa;

  while (1)
  {
    //Clear previous result
    dm_report.link_loss = 0;
    dm_report.rssi_local = 0;
    dm_report.rssi_remote = 0;
    dm_report.txpwr_local = 0;
    dm_report.txpwr_remote = 0;
    dm_report.quality = 100;
    dm_report.distance_estimates.mcpd.ifft = 0;
    dm_report.distance_estimates.mcpd.phase_slope = 0;
    dm_report.distance_estimates.mcpd.rssi_openspace = 0;
    dm_report.distance_estimates.mcpd.best = 0;
    for(int i=0;i<80;i++){
      dm_report.iq_tones->i_local[i] =0;
      dm_report.iq_tones->q_local[i] =0;
      dm_report.iq_tones->i_remote[i] =0;
      dm_report.iq_tones->q_remote[i] =0;
    }
    for(int i=0;i<80;i++){
      dm_report.tone_sinr_indicators.sinr_indicator_local[i] =0;
      dm_report.tone_sinr_indicators.sinr_indicator_remote[i] =0;
    }

    //- Wait for a character, any character
    uart_init();
    char c = 0;
    uart_get_char(&c);
    uart_uninit();

    //- Execute a ranging
    nrf_dm_status_t status = nrf_dm_configure(&dm_config);
    debug_start();
    uint32_t timeout_us = 0.5e6;
    status     = nrf_dm_proc_execute(timeout_us);
    debug_stop();

    float distance = 0;

    if(status == NRF_DM_STATUS_SUCCESS){
      nrf_dm_populate_report(&dm_report);
      nrf_dm_quality_t quality = nrf_dm_calc(&dm_report);

      //- TODO: Something does not work with this yet, some missing symbols
      //distance = nrf_dm_high_precision_calc(&dm_report);

    }else{
      //- Set quality to 100 if it's a failure
      dm_report.quality = 100;
      debug_pulse(10);
    }

    //- Send report to UART
    uart_init();
    nrf_dm_report_to_json(&dm_report,distance);
    uart_uninit();

  }
}
