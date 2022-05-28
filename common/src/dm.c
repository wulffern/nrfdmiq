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




#define DBGPIN_1  30
#define DBGPIN_2  31

void debug_init(){

  // Configure GPIO pin as output with standard drive strength.
  NRF_GPIO->PIN_CNF[DBGPIN_2] =
    (GPIO_PIN_CNF_DIR_Output << GPIO_PIN_CNF_DIR_Pos) | (GPIO_PIN_CNF_DRIVE_S0S1 << GPIO_PIN_CNF_DRIVE_Pos)
    | (GPIO_PIN_CNF_INPUT_Connect << GPIO_PIN_CNF_INPUT_Pos) | (GPIO_PIN_CNF_PULL_Disabled << GPIO_PIN_CNF_PULL_Pos)
    | (GPIO_PIN_CNF_SENSE_Disabled << GPIO_PIN_CNF_SENSE_Pos);

  // Configure GPIO pin as output with standard drive strength.
  NRF_GPIO->PIN_CNF[DBGPIN_1] =
    (GPIO_PIN_CNF_DIR_Output << GPIO_PIN_CNF_DIR_Pos) | (GPIO_PIN_CNF_DRIVE_S0S1 << GPIO_PIN_CNF_DRIVE_Pos)
    | (GPIO_PIN_CNF_INPUT_Connect << GPIO_PIN_CNF_INPUT_Pos) | (GPIO_PIN_CNF_PULL_Disabled << GPIO_PIN_CNF_PULL_Pos)
      | (GPIO_PIN_CNF_SENSE_Disabled << GPIO_PIN_CNF_SENSE_Pos);


  //NRF_GPIOTE->CONFIG[0] = GPIOTE_CONFIG_MODE_Task | (DBGPIN_2 << GPIOTE_CONFIG_PSEL_Pos)
  //                        | (GPIOTE_CONFIG_POLARITY_Toggle << GPIOTE_CONFIG_POLARITY_Pos)
  //    | (GPIOTE_CONFIG_OUTINIT_High << GPIOTE_CONFIG_OUTINIT_Pos);

  //NRF_PPI->FORK[0].TEP = (uint32_t)&NRF_GPIOTE->TASKS_OUT[0];

}

static void debug_set(uint32_t pin)
{

  NRF_GPIO->OUTSET = 0x1 << pin;

}

static void debug_clear(uint32_t pin)
{

  NRF_GPIO->OUTCLR = 0x1 << pin;

}

void debug_start(){
    debug_set(DBGPIN_2);
}

void debug_stop(){
    debug_clear(DBGPIN_2);
}


void dm_init(){
    //- Setup Nordic Distance Toolbox

  uint8_t ppi_ch[2] = {0 ,1 };
  nrf_dm_ppi_config_t ppi_conf = {
  .ppi_chan_count = 1,
  .ppi_chan = &ppi_ch[0],
};

  nrf_dm_antenna_config_t ant_cfg = NRF_DM_DEFAULT_SINGLE_ANTENNA_CONFIG ;
  nrf_dm_init(&ppi_conf,&ant_cfg,NRF_TIMER1);
}


void debug_pulse(int delay){
  debug_set(DBGPIN_1);
  volatile int z = 0;
   for(int i=0;i<delay;i++){ z+= 1;}

  debug_clear(DBGPIN_1);
}


static void m_nrfx_clock_event_handler(nrfx_clock_evt_type_t event)
{
  (void) event;
}

void dm_clock_init(void)
{
#ifdef NRF_CLOCK_NS
  #define NRF_CLOCK NRF_CLOCK_NS
#endif

  nrfx_clock_init(m_nrfx_clock_event_handler);
  nrfx_clock_start(NRF_CLOCK_DOMAIN_HFCLK);

  while(true)
  {
    nrf_clock_hfclk_t src;
    if(nrfx_clock_is_running(NRF_CLOCK_DOMAIN_HFCLK, &src) && (src == NRF_CLOCK_HFCLK_HIGH_ACCURACY))
    {
      break;
    }
  }
}
