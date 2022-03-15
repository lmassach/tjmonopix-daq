#
# ------------------------------------------------------------
# Copyright (c) All rights reserved
# SiLab, Institute of Physics, University of Bonn
# ------------------------------------------------------------
#

import yaml
import logging
import os
import time
import numpy as np
import pkg_resources
from collections import defaultdict

from bitarray import bitarray
from basil.dut import Dut

ROW = 224
COL = 112

# Directory for log file. Create if it does not exist
DATDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output_data")
if not os.path.exists(DATDIR):
    os.makedirs(DATDIR)

VERSION = pkg_resources.get_distribution("tjmonopix-daq").version

''' Set up main logger '''
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.getLogger('basil.HL.RegisterHardwareLayer').setLevel(logging.WARNING)

logging.basicConfig(
    format="%(asctime)s [%(levelname)-5.5s] (%(threadName)-10s) %(message)s")
logger = logging.getLogger('TJMONOPIX')
logger.setLevel(logging.INFO)

fileHandler = logging.FileHandler(os.path.join(DATDIR, time.strftime("%Y%m%d-%H%M%S.log")))
logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] (%(threadName)-10s) %(message)s")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)


class TJMonoPix(Dut):

    """ Map hardware IDs for board identification """
    hw_map = {
        0: 'SIMULATION',
        1: 'MIO2',
    }

    def __init__(self, conf=None,no_power_reset=False):
        if not conf:
            proj_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            conf = os.path.join(proj_dir, 'tjmonopix' + os.sep + 'tjmonopix.yaml')

        self.ROW = 224
        self.COL = 112

        logger.debug("Loading configuration file from {}".format(conf))

        if isinstance(conf,str):
            with open(conf) as f:
                conf=yaml.safe_load(f)
            for i,e in enumerate(conf["hw_drivers"]):
                if e["type"]=="GPAC":
                    #print conf["hw_drivers"][i].keys()
                    if "init" in conf["hw_drivers"][i].keys():
                        conf["hw_drivers"][i]["init"]["no_power_reset"]=no_power_reset
                    else:
                        conf["hw_drivers"][i]["init"]={"no_power_reset":no_power_reset}
                    break

        super(TJMonoPix, self).__init__(conf)
        self.conf_flg = 1
        self.SET = {'VDDA': None, 'VDDP': None, 'VDDA_DAC': None, 'VDDD': None,
                    'VPCSWSF': None, 'VPC': None, 'BiasSF': None, 'INJ_LO': None, 'INJ_HI': None,
                    'DACMON_ICASN': None, 'fl': None}
        self.debug = 0

    def get_daq_version(self):
        ret = self['intf'].read(0x0000, 2)
        fw_version = str('%s.%s' % (ret[1], ret[0]))

        ret = self['intf'].read(0x0002, 2)
        board_version = ret[0] + (ret[1] << 8)

        return fw_version, board_version

    def init(self, fl="EN_PMOS"):
        super(TJMonoPix, self).init()

        self.fw_version, self.board_version = self.get_daq_version()
        logger.info('Found board %s running firmware version %s' % (self.board_version, self.fw_version))

        # do this before powering up
        self['CONF_SR'].set_size(3925)
        self['CONF']['DEF_CONF_N'] = 0

        self.switch_flavor(fl)
        self.power_on()

        self['CONF']['RESET_BCID'] = 1
        self['CONF']['RESET'] = 1
        self['CONF'].write()

        self['CONF']['EN_BX_CLK'] = 1
        self['CONF']['EN_OUT_CLK'] = 1
        self['CONF'].write()

        self['CONF']['RESET_BCID'] = 0
        self['CONF']['RESET'] = 0
        self['CONF'].write()

        self.default_conf()
        self.write_conf()

        self['CONF']['DEF_CONF_N'] = 1
        self['CONF'].write()

        logging.info(str(self.get_power_status()))

    def default_conf(self):
        self['CONF_SR']['nEN_HITOR_OUT'].setall(True)
        self['CONF_SR']['EN_HITOR_OUT'].setall(True)
        self['CONF_SR']['nEN_OUT'].setall(True)

        self['CONF_SR']['EN_OUT'].setall(True)  ## active low
        self['CONF_SR']['EN_HV'].setall(False)
        self['CONF_SR']['EN_COMP'].setall(False)
        self['CONF_SR']['EN_PMOS'].setall(False)
        self['CONF_SR']['EN_PMOS_NOSF'].setall(False)
        self['CONF_SR']['EN_TEST_PATTERN'].setall(False)

        self['CONF_SR']['MASKD'].setall(False)
        self['CONF_SR']['MASKH'].setall(False)
        self['CONF_SR']['MASKV'].setall(False)

        self['CONF_SR']['SWCNTL_VRESET_P'] = 0
        self['CONF_SR']['SWCNTL_VRESET_D'] = 0
        self['CONF_SR']['SWCNTL_VL'] = 0
        self['CONF_SR']['SWCNTL_VH'] = 0
        self['CONF_SR']['SWCNTL_VCLIP'] = 0
        self['CONF_SR']['SWCNTL_VCASN'] = 0
        self['CONF_SR']['SWCNTL_ITHR'] = 0
        self['CONF_SR']['SWCNTL_IRESET'] = 0
        self['CONF_SR']['SWCNTL_IREF'] = 0
        self['CONF_SR']['SWCNTL_IDB'] = 0
        self['CONF_SR']['SWCNTL_ICASN'] = 0
        self['CONF_SR']['SWCNTL_IBIAS'] = 0
        self['CONF_SR']['SWCNTL_DACMONV'] = 0
        self['CONF_SR']['SWCNTL_DACMONI'] = 0

        self['CONF_SR']['SET_IBUFN_L'] = 0b1001
        self['CONF_SR']['SET_IBUFP_L'] = 0b0101
        self['CONF_SR']['SET_IBUFP_R'] = 0b0101
        self['CONF_SR']['SET_IBUFN_R'] = 0b1001

        self['CONF_SR']['SET_VCLIP'].setall(False)
        self['CONF_SR']['SET_VRESET_D'].setall(False)
        self['CONF_SR']['SET_VRESET_D'][45] = 1
        self['CONF_SR']['SET_VCASN'].setall(False)
        self['CONF_SR']['SET_VCASN'][40] = 1
        self['CONF_SR']['SET_VL'].setall(False)
        self['CONF_SR']['SET_VL'][44] = 1
        self['CONF_SR']['SET_VH'].setall(False)
        self['CONF_SR']['SET_VH'][79] = 1
        self['CONF_SR']['SET_VRESET_P'].setall(False)
        self['CONF_SR']['SET_VRESET_P'][16] = 1

        self.set_icasn_dacunits(0,0)
        self.set_vreset_dacunits(35,0)
        self.set_ireset_dacunits(2,1,0)
        self.set_ithr_dacunits(5,0)
        self.set_idb_dacunits(50,0)
        self.set_ibias_dacunits(45,1)

        self['CONF_SR']['DIG_MON_SEL'].setall(False)

        self['CONF_SR']['INJ_ROW'].setall(False)
        self['CONF_SR']['INJ_IN_MON_R'] = 0
        self['CONF_SR']['INJ_IN_MON_L'] = 0
        self['CONF_SR']['COL_PULSE_SEL'].setall(False)

    def write_conf(self):
        self['CONF_SR'].write()
        while not self['CONF_SR'].is_ready:
            time.sleep(0.001)
        self.conf_flg = 0

    def load_config(self, filename):
        with open(filename) as f:
            conf = yaml.safe_load(f)
        self.SET['fl'] = conf["SET"]["fl"]
        if fl == "EN_PMOS_NOSF":
            self.fl_n = 0
        elif fl == "EN_PMOS":
            self.fl_n = 1
        elif fl == "EN_COMP":
            self.fl_n = 2
        elif fl == "EN_HV":
            self.fl_n = 3
        self['CONF'] = conf["CONF"]
        self['CONF'].write()
        self.default_conf()
        self.write_conf()
        self.reset_ibias()
        self.power_on(VDDA=conf["SET"]["VDDA"],
                      VDDP=conf["SET"]["VDDP"],
                      VDDA_DAC=conf["SET"]["VDDA_DAC"],
                      VDDD=conf["SET"]["VDDD"],
                      VPCSWSF=conf["SET"]["VPCSWSF"],
                      VPC=conf["SET"]["VPC"],
                      BiasSF=conf["SET"]["BiasSF"])
        self['CONF_SR']=conf['CONF_SR']
        self.write_conf()
        self.reset_ibias()

    def save_config(self, filename=None):
        if filename is None:
            filename = os.path.join(DATDIR, time.strftime("config_%s_%Y%m%d-%H%M%S.yaml"%fmt))
        conf = self.get_configuration()
        conf["SET"] = self.SET
        with open(filename, "w") as f:
            yaml.dump(conf, f)
        logging.info("save_config filename: %s" % filename)
        return filename

    def power_on(self, VDDA=1.8, VDDP=1.8, VDDA_DAC=1.8, VDDD=1.8, VPCSWSF=0.5, VPC=1.3, BiasSF=100):
        # Set power

        # Sense resistor is 0.1Ohm, so 300mA=60mA*5
        self['VDDP'].set_current_limit(60, unit='mA')
        self['VDDP'].set_voltage(VDDP, unit='V')
        self.SET["VDDP"] = VDDP

        self['VPCSWSF'].set_voltage(VPCSWSF, unit='V')
        self.SET["VPCSWSF"] = VPCSWSF

        self['VPC'].set_voltage(VPC, unit='V')
        self.SET["VPC"] = VPC

        self['BiasSF'].set_current(BiasSF, unit='uA')
        self.SET["BiasSF"] = BiasSF

        self['VDDA'].set_voltage(VDDA, unit='V')
        self.SET["VDDA"] = VDDA
        self['VDDA'].set_enable(True)
        time.sleep(0.01)

        self['VDDP'].set_enable(True)

        self['VDDA_DAC'].set_voltage(VDDA_DAC, unit='V')
        self['VDDA_DAC'].set_enable(True)
        self.SET["VDDA_DAC"] = VDDA_DAC

        self['VDDD'].set_voltage(VDDD, unit='V')
        self['VDDD'].set_enable(True)
        self.SET["VDDD"] = VDDD

        #DACMON_ICASN = 0
        #self['DACMON_ICASN'].set_current(DACMON_ICASN, unit='uA')
        #self.SET["DACMON_ICASN"] = DACMON_ICASN

    def power_off(self):
        # Deactivate all
        for pwr in ['VDDP', 'VDDD', 'VDDA', 'VDDA_DAC']:
            self[pwr].set_enable(False)

    def get_power_status(self, printen=False):
        status = {}
        for pwr in ['VDDP', 'VDDD', 'VDDA', 'VDDA_DAC', 'VPCSWSF', 'VPC', 'BiasSF']:
            status[pwr + ' [V]'] = self[pwr].get_voltage(unit='V')
            if pwr in ["VDDP", "VDDD", "VDDA", "VDDA_DAC"]:
                 status[pwr + ' [mA]'] = 5 * self[pwr].get_current(unit='mA')
                 status[pwr + ' OC'] = self[pwr].get_over_current()
            else:
                 status[pwr + ' [mA]'] = self[pwr].get_current(unit='mA')
        if printen:
            for k in sorted(status):
                print("%s = %s" % (k, status[k]))
        return status

    def set_inj_all(self,vh=79,vl=44,inj_delay=800,inj_width=250,inj_n=100,inj_phase=0):
        self["inj"].reset()
        self["inj"].set_width(inj_width)
        self["inj"].set_delay(inj_delay)
        self["inj"].set_repeat(inj_n)
        if inj_phase > -1 :
            self["inj"].set_phase(inj_phase)
        self["inj"].set_en(0)
        self.set_vl_dacunits(vl,1)
        self.set_vh_dacunits(vh,1)
        self.write_conf()

    def inject(self):
        self["inj"].start()

    def interpret_data(self, raw_data):
        hit_data_sel = ((raw_data & 0xF0000000) == 0)
        hit_data = raw_data[hit_data_sel]
        hit_dtype = np.dtype(
            [("col", "<u1"), ("row", "<u2"), ("le", "<u1"), ("te", "<u1"), ("noise", "<u1")])
        ret = np.empty(hit_data.shape[0], dtype=hit_dtype)

        ret['col'] = 2 * (hit_data & 0x3F) + (((hit_data & 0x7FC0) >> 6) // 256)
        ret['row'] = ((hit_data & 0x7FC0) >> 6) % 256
        ret['te'] = (hit_data & 0x1F8000) >> 15
        ret['le'] = (hit_data & 0x7E00000) >> 21
        ret['noise'] = (hit_data & 0x8000000) >> 27
        return ret

    def mask(self, flavor, col, row):
        assert 0 <= flavor <= 3, 'Flavor must be between 0 and 3'
        assert 0 <= col <= 111, 'Column must be between 0 and 111'
        assert 0 <= row <= 223, 'Row must be between 0 and 223'
        mcol = flavor * 112 + col
        md = mcol - row if (mcol - row) >= 0 else 448 + mcol - row
        self['CONF_SR']['MASKD'][md] = False
        self['CONF_SR']['MASKV'][mcol] = False
        self['CONF_SR']['MASKH'][row] = False

    def enable_injection(self, flavor, col, row):
        """ Enables injection in one selected pixel

        Parameters:
        -----------
        flavor: int
            Flavor number (PMOS: 1, HV: 3)
        col: int
        row: int
        """
        if flavor > 3 or flavor < 0:
            raise ValueError("Flavor number must be between 0 and 3")
        if col < 0 or col > 112:
            raise ValueError("Column number must be between 0 and 111")
        if row < 0 or row > 223:
            raise ValueError("Row number must be between 0 and 223")

        self['CONF_SR']['COL_PULSE_SEL'][(flavor * 112) + col] = 1
        self['CONF_SR']['INJ_ROW'][row] = 1

    def prepare_injection_mask(self, start_col=0, stop_col=112, step_col=1, width_col=56, start_row=0, stop_row=224, step_row=1, width_row=4):
        """ Start col/row: first col/row
        Stop col/row: last col/row
        Step col/row: col/row step to inject
        Width col/row: Step width to inject into cols/rows at same time
        """
        n_masks = min(stop_col - start_col, width_col) * min(stop_row - start_row, width_row) / (step_col * step_row)
        masks = []

        for i in range(n_masks):
            ba_col = 448 * bitarray('0')
            ba_row = 224 * bitarray('0')

            ba_col[self.fl_n * 112 + start_col + (i // (width_row // step_row)) * step_col:self.fl_n * 112 + stop_col:width_col] = True
            ba_row[start_row + (i % (width_row // step_row) * step_row):stop_row:width_row] = True

            masks.append({'col': ba_col, 'row': ba_row})
        return masks

    def enable_hitor(self, flavor, col,row):
        """ Enables hit or in given column for given flavor

        Parameters:
        -----------
        flavor: int
            Flavor number (PMOS:1, HV: 3)
        col: int
            Column number to activate hitor for
        """
        if flavor > 3 or flavor < 0:
            raise ValueError("Flavor number must be between 0 and 3")
        if col < 0 or col > 112:
            raise ValueError("Column number must be between 0 and 111")
        self['CONF_SR']['EN_HITOR_OUT'][flavor] = 0 # active low
        self['CONF_SR']['DIG_MON_SEL'][(flavor * 112) + col] = 1
        self['CONF_SR']['MASKH'][row] = 0 # active low to HITOR (besure enable pixel with D or V)

    def enable_pixel(self,flavor,col,row,mask=[]):
        if flavor!=self.fl_n:
            logger.warn('you are trying to enable fl=%d but %d is set'%(flavor,self.fl_n))
        if flavor==0:
            fl="EN_PMOS_NOSF"
        elif flavor==1:
            fl="EN_PMOS"
        elif flavor==2:
            fl="EN_COMP"
        elif flavor==3:
            fl="EN_HV"
        if col<0:
            self['CONF_SR']['MASKD'].setall(True)
            self['CONF_SR']['MASKH'].setall(True)
            self['CONF_SR']['MASKV'].setall(True)
            self['CONF_SR'][fl].setall(True)
        else:
            mcol = flavor * 112 + col
            md = mcol - row if (mcol - row) >= 0 else 448 + mcol - row
            self['CONF_SR']['MASKD'][md]=True
            self['CONF_SR'][fl][col/2]=True
        self['CONF_SR']["EN_OUT"][flavor]=False
        for m in mask:
            self.mask(*m)

    def enable_analog(self,col="all",row=-1):
        if col=="all":
            self["CONF_SR"]["INJ_IN_MON_L"] =True
            self["CONF_SR"]["INJ_IN_MON_R"] =True
            self["CONF_SR"]["INJ_ROW"][223] =True
            self["CONF_SR"]["INJ_ROW"][222] =True
            self["CONF_SR"]["INJ_ROW"][221] =True
            self["CONF_SR"]["INJ_ROW"][220] =True
        elif col=="l":
            self["CONF_SR"]["INJ_IN_MON_L"] =True
        elif col=="r":
            self["CONF_SR"]["INJ_IN_MON_R"] =True
        if row == -1:
            self["CONF_SR"]["INJ_ROW"][223] =True
            self["CONF_SR"]["INJ_ROW"][222] =True
            self["CONF_SR"]["INJ_ROW"][221] =True
            self["CONF_SR"]["INJ_ROW"][220] =True
        else:
            self["CONF_SR"]["INJ_ROW"][220+row] =True

    def switch_flavor(self,fl):
        if fl[:3]!="EN_":
            fl="EN_%s"%fl
        if fl == "EN_HV" or fl == 'EN_PMOS':
            self['CONF']['AB_SELECT'] = True
        else:
            self['CONF']['AB_SELECT'] = False

        self.SET['fl'] = fl
        if fl == "EN_PMOS_NOSF":
            self.fl_n = 0
        elif fl == "EN_PMOS":
            self.fl_n = 1
        elif fl == "EN_COMP":
            self.fl_n = 2
        elif fl == "EN_HV":
            self.fl_n = 3

        self['CONF'].write()

    def set_ibias_dacunits(self, dacunits, printen=False):
        assert 0 <= dacunits <= 127, 'Dac Units must be between 0 and 127'
        low = (128-(dacunits+1))/2
        high = ((dacunits+1)/2)+63
        self['CONF_SR']['SET_IBIAS'].setall(False)
        self['CONF_SR']['SET_IBIAS'][high:low] = (high - low + 1) * bitarray([True])
        ibias = 1400.0 * ((dacunits + 1) / 128.0)
        if printen:
            logger.info('ibias = %s', dacunits)
            logger.info('ibias = %s nA', ibias)
        return ibias

    def reset_ibias(self):
        """ To eliminate oscillations, set ibias to 0 and back to previous value
        """
        ibias = self['CONF_SR']['SET_IBIAS'][:]
        self.set_ibias_dacunits(0, 0)
        self.write_conf()
        self['CONF_SR']['SET_IBIAS'][:] = ibias
        self.write_conf()

    def set_idb_dacunits(self, dacunits, printen=False):
        dacunits=int(dacunits)
        assert 0 <= dacunits <= 127, 'Dac Units must be between 0 and 127 but %d'%dacunits
        low = (128-(dacunits+1))/2
        high = ((dacunits+1)/2)+63
        self['CONF_SR']['SET_IDB'].setall(False)
        self['CONF_SR']['SET_IDB'][high:low] = (high - low + 1) * bitarray([True])
        idb = 2240.0 * ((dacunits + 1) / 128.0)
        if printen:
            logger.info('idb = %s', dacunits)
            logger.info('idb = %s nA', idb)
        return idb

    def set_ithr_dacunits(self, dacunits, printen=False):
        dacunits=int(dacunits)
        assert 0 <= dacunits <= 127, 'Dac Units must be between 0 and 127'
        low = (128-(dacunits+1))/2
        high = ((dacunits+1)/2)+63
        self['CONF_SR']['SET_ITHR'].setall(False)
        self['CONF_SR']['SET_ITHR'][high:low] = (high - low + 1) * bitarray([True])
        ithr = 17.5 * ((dacunits + 1) / 128.0)
        if printen:
            logger.info('ithr = %s', dacunits)
            logger.info('ithr = %s nA', ithr)
        return ithr


    def set_icasn_dacunits(self, dacunits, printen=False):
        assert -1 <= dacunits <= 127, 'Dac Units must be between 0 and 127'
        self['CONF_SR']['SET_ICASN'].setall(False)
        if dacunits>-1:
            low = (128-(dacunits+1))/2
            high = ((dacunits+1)/2)+63
            self['CONF_SR']['SET_ICASN'][high:low] = (high - low + 1) * bitarray([True])
        icasn = 560.0 * ((dacunits + 1) / 128.0)
        if printen:
            logger.info('icasn = %s', dacunits)
            logger.info('icasn = %s nA', icasn)
        return icasn

    def set_ireset_dacunits(self, dacunits, mode, printen=False):
        assert 0 <= dacunits <= 127, 'Dac Units must be between 0 and 127'
        assert 0 <= mode <= 1, 'Mode must be 0 (low leakage) or 1 (high leakage)'
        low = (128-(dacunits+1))/2
        high = ((dacunits+1)/2)+63
        self['CONF_SR']['SET_IRESET_BIT'] = mode
        self['CONF_SR']['SET_IRESET'].setall(False)
        self['CONF_SR']['SET_IRESET'][high:low] = (high - low + 1) * bitarray([True])
        if (mode == 1):
            ireset = 4.375 * ((dacunits + 1) / 128.0)
            if printen:
                logger.info('ireset = ' + str(dacunits) + ' high leakage mode')
                logger.info('ireset = ' + str(ireset) + 'nA, high leakage mode')
            return ireset
        else:
            ireset = 43.75 * ((dacunits + 1) / 128.0) * 0.001
            if printen:
                logger.info('ireset = ' + str(dacunits) + ' low leakage mode')
                logger.info('ireset = ' + str(ireset) + 'nA, low leakage mode')
            return ireset

    def set_vreset_dacunits(self, dacunits, printen=False):
        assert 0 <= dacunits <= 127, 'Dac Units must be between 0 and 127'
        self['CONF_SR']['SET_VRESET_P'].setall(False)
        self['CONF_SR']['SET_VRESET_P'][dacunits] = True
        vreset = ((1.8 / 127.0) * dacunits + 0.555)
        if printen:
            logger.info('vreset = ' + str(vreset) + 'V')
        return vreset

    def set_vh_dacunits(self, dacunits, print_en=False):
        dacunits=int(dacunits)
        assert 0 <= dacunits <= 127, 'Dac Units must be between 0 and 127'
        self['CONF_SR']['SET_VH'].setall(False)
        self['CONF_SR']['SET_VH'][dacunits] = True
        vh = ((1.8 / 127.0) * dacunits + 0.385)
        if print_en:
                logger.info('vh = ' + str(vh) + 'V')
        return vh

    def get_idb_dacunits(self):
        arg=np.argwhere(np.array(list(self['CONF_SR']['SET_IDB'].to01()),dtype=int))
        low=arg[0,0]
        high=arg[-1,0]
        dacunits_low=128-low*2
        dacunits_high= (high -(128 // 2))*2
        return (dacunits_low+dacunits_high)/2

    def get_vh_dacunits(self):
        for i in range(0, 128):
            if self['CONF_SR']['SET_VH'][i] is True:
                return i
        return -1

    def set_vl_dacunits(self, dacunits, printen=False):
        dacunits=int(dacunits)
        assert 0 <= dacunits <= 127, 'Dac Units must be between 0 and 127'
        self['CONF_SR']['SET_VL'].setall(False)
        self['CONF_SR']['SET_VL'][dacunits] = True
        if printen:
                logger.info('vl = ' + str(((1.8 / 127.0) * dacunits + 0.385)) + 'V')

    def get_vl_dacunits(self):
        for i in range(0, 128):
            if self['CONF_SR']['SET_VL'][i] is True:
                return i
        return -1

    def set_vcasn_dac_dacunits(self, dacunits, printen=False):
        assert 0 <= dacunits <= 127, 'Dac Units must be between 0 and 127'
        self['CONF_SR']['SET_VCASN'].setall(False)
        self['CONF_SR']['SET_VCASN'][dacunits] = True
        if printen:
            logger.info('vcasn = ' + str(dacunits))
            logger.info('vcasn = ' + str(((1.8 / 127.0) * dacunits)) + 'V')

    def get_conf_sr(self,mode="mwr"):
        """ mode:'w' get values in FPGA write register (output to SI_CONF)
                 'r' get values in FPGA read register (input from SO_CONF)
                 'm' get values in cpu memory (data in self['CONF_SR'])
                 'mrw' get all
        """
        size=self['CONF_SR'].get_size()
        r=size%8
        byte_size=size/8
        if r!=0:
            r=8-r
            byte_size=byte_size+1
        data={"size":size}
        if "w" in mode:
           data["write_reg"]=self["CONF_SR"].get_data(addr=0,size=byte_size).tostring()
        if "r" in mode:
           data["read_reg"]=self["CONF_SR"].get_data(size=byte_size).tostring()
        if "m" in mode:
           a=bitarray("0000000")[0:r]+self["CONF_SR"][:]
           data["memory"]=a[::-1].tobytes()
        return data

############################## SET data readout ##############################

    def cleanup_fifo(self, n=10):
        for _ in range(n):
            time.sleep(0.1)
            self['fifo'].reset()

    def set_tlu(self, tlu_delay=8):
        self["tlu"]["RESET"] = 1
        self["tlu"]["TRIGGER_MODE"] = 3
        self["tlu"]["EN_TLU_VETO"] = 0
        self["tlu"]["MAX_TRIGGERS"] = 0
        self["tlu"]["TRIGGER_COUNTER"] = 0
        self["tlu"]["TRIGGER_LOW_TIMEOUT"] = 0
        self["tlu"]["TRIGGER_VETO_SELECT"] = 0
        self["tlu"]["TRIGGER_THRESHOLD"] = 0
        self["tlu"]["DATA_FORMAT"] = 2
        self["tlu"]["TRIGGER_HANDSHAKE_ACCEPT_WAIT_CYCLES"] = 20
        self["tlu"]["TRIGGER_DATA_DELAY"] = tlu_delay
        self["tlu"]["TRIGGER_SELECT"] = 0
        self["timestamp_tlu"]["RESET"] = 1
        self["timestamp_tlu"]["EXT_TIMESTAMP"] = 1
        self["timestamp_tlu"]["ENABLE_TRAILING"] = 0
        logging.info("set_tlu: tlu_delay=%d" % tlu_delay)

        self["timestamp_tlu"]["ENABLE_EXTERN"] = 1
        self["tlu"]["TRIGGER_ENABLE"] = 1

    def stop_tlu(self):
        self["tlu"]["TRIGGER_ENABLE"] = 0
        self["timestamp_tlu"]["ENABLE_EXTERN"] = 0
        lost_cnt = self["timestamp_tlu"]["LOST_COUNT"]
        if lost_cnt != 0:
            logging.warn("stop_tlu: error cnt=%d" % lost_cnt)

    def set_timestamp(self, src="rx1"):
        self["timestamp_{}".format(src)].reset()
        self["timestamp_{}".format(src)]["EXT_TIMESTAMP"] = True
        if src == "rx1":
            self["timestamp_rx1"]["ENABLE_TRAILING"] = 0
            self["timestamp_rx1"]["ENABLE"] = 1
        elif src == "mon":
            self["timestamp_mon"]["ENABLE_TRAILING"] = 1
            self["timestamp_mon"]["ENABLE"] = 1
        elif src == "inj":
            self["timestamp_inj"]["ENABLE"] = 1
        elif src == "tlu":
            self["timestamp_tlu"]["ENABLE_TRAILING"] = 0
            self["timestamp_tlu"]["ENABLE_EXTERN"] = 1

        logging.info("Set timestamp: src={}".format(src))

    def stop_timestamp(self, src="rx1"):
        self["timestamp_{}".format(src)]["ENABLE"] = 0
        lost_cnt = self["timestamp_{}".format(src)]["LOST_COUNT"]
        if lost_cnt != 0:
            logging.warn("Stop timestamp: src={} lost_cnt={:d}".format(src, lost_cnt))
        return lost_cnt

    def set_monoread(self, start_freeze=64, start_read=66, stop_read=68, stop_freeze=100, stop=105,
    #def set_monoread(self, start_freeze=57, start_read=60, stop_read=62, stop_freeze=95, stop=100,
                     en=True, read_shift=52, sync_timestamp=True,disable_gray_decorder=False):
        self['CONF']['EN_RST_BCID_WITH_TIMESTAMP'] = sync_timestamp
        self['CONF']['RESET_BCID'] = 1
        self['CONF'].write()

        self['data_rx'].reset()
        self['data_rx'].DISSABLE_GRAY_DECODER=disable_gray_decorder
        self['data_rx'].CONF_START_FREEZE = start_freeze  # default 57
        self['data_rx'].CONF_STOP_FREEZE = stop_freeze  # default 95
        self['data_rx'].CONF_START_READ = start_read  # default 60
        self['data_rx'].CONF_STOP_READ = stop_read  # default 62
        self['data_rx'].CONF_STOP = stop  # default 100
        self['data_rx'].CONF_READ_SHIFT = read_shift  # default 100

        self.cleanup_fifo(2)
        self['CONF']['RESET_BCID'] = 0
        self['CONF'].write()
        self['data_rx'].set_en(en)

    def stop_monoread(self):
        self['data_rx'].set_en(False)
        lost_cnt = self["data_rx"]["LOST_COUNT"]
        if lost_cnt != 0:
            logging.warn("stop_monoread: error cnt=%d" % lost_cnt)

    def stop_all(self):
        self.stop_tlu()
        self.stop_monoread()
        self.stop_timestamp("rx1")
        self.stop_timestamp("inj")
        self.stop_timestamp("mon")

########################## pcb components #####################################
    def get_temperature(self, n=10):
        # TODO: Why is this needed? Should be handled by basil probably
        vol = self["NTC"].get_voltage()
        if not (vol > 0.5 and vol < 1.5):
            for i in np.arange(2, 200, 2):
                self["NTC"].set_current(i, unit="uA")
                time.sleep(0.1)
                vol = self["NTC"].get_voltage()
                if self.debug != 0:
                    print("temperature() set_curr=", i, "vol=", vol)
                if vol > 0.7 and vol < 1.3:
                    break
            if abs(i) > 190:
                logging.warn("temperature() NTC error")

        temp = np.empty(n)
        for i in range(len(temp)):
            temp[i] = self["NTC"].get_temperature("C")
        return np.average(temp[temp != float("nan")])


    def get_disabled_pixel(self,maskV=None,maskH=None,maskD=None):
        if maskV is None:
            maskV = self['CONF_SR']['MASKV']
        if maskH is None:
            maskH = self['CONF_SR']['MASKH']
        if maskD is None:
            maskD = self['CONF_SR']['MASKD']

        mask = np.ones([COL * 4, ROW], dtype=int) * 0x7
        for i in range(COL * 4):
            for j in range(ROW):
                if maskV[i] is False:
                    mask[i, j] = (mask[i, j] & 0x6)
                if maskH[j] is False:
                    mask[i, j] = (mask[i, j] & 0x5)
                if (i - j) >= 0 and maskD[i - j] is False:
                    mask[i, j] = (mask[i, j] & 0x3)
                elif (i - j) < 0 and maskD[448 + i - j] is False:
                    mask[i, j] = (mask[i, j] & 0x3)
        return mask
    def get_pixel_status(self,mode="all",mask=None):
        if mask is None:
          mask = np.ones([4, COL, ROW], dtype=int) * 0x1FF
          for k in range(4):
            for l in range(COL):
              i=k*COL+l
              for j in range(ROW):
                if self['CONF_SR']['MASKV'][i] is False:
                    mask[k, l, j] = mask[k, l, j] & (0x1FF-0x1)
                if self['CONF_SR']['MASKH'][j] is False:
                    mask[k, l, j] = mask[k, l, j] & (0x1FF-0x2)
                if (i - j) >= 0 and self['CONF_SR']['MASKD'][i - j] is False:
                    mask[k, l, j] = mask[k, l, j] & (0x1FF-0x4)
                elif (i - j) < 0 and self['CONF_SR']['MASKD'][448 + i - j] is False:
                    mask[k, l, j] = mask[k, l, j] & (0x1FF-0x4)

                if k==0 and self["CONF_SR"]["EN_PMOS_NOSF"][l/2] is False:
                       mask[k, l, j]=mask[k, l, j] & (0x1FF-0x8)
                elif k==1 and self["CONF_SR"]["EN_PMOS"][l/2] is False:
                       mask[k, l, j]=mask[k, l, j] & (0x1FF-0x8)
                elif k==2 and self["CONF_SR"]["EN_COMP"][l/2] is False:
                       mask[k, l, j]=mask[k, l, j] & (0x1FF-0x8)
                elif k==3 and self["CONF_SR"]["EN_HV"][l/2] is False:
                       mask[k, l, j]=mask[k, l, j] & (0x1FF-0x8)
                if self['CONF_SR']['EN_OUT'][k]: # active low len=4
                       mask[k, l, j]=mask[k, l, j] & (0x1FF-0x10)

                if self['CONF_SR']['DIG_MON_SEL'][i] is False: #len=448
                       mask[k, l, j]=mask[k, l, j] & (0x1FF-0x20)
                if self['CONF_SR']['EN_HITOR_OUT'][k]: # active low len=4
                       mask[k, l, j]=mask[k, l, j] & (0x1FF-0x40)

                if self['CONF_SR']['COL_PULSE_SEL'][i] is False:  #len=448
                       mask[k, l, j]=mask[k, l, j] & (0x1FF-0x80)
                if self['CONF_SR']['INJ_ROW'][j] is False: #len
                       mask[k, l, j]=mask[k, l, j] & (0x1FF-0x100)

        if mode=="preamp":
            return (mask & 0x7) !=0
        elif mode=="monoread":
            return np.bitwise_and((mask & 0x7)!=0 ,(mask & 0x18)==0x18)
        elif mode=="mon":
            return np.bitwise_and((mask & 0x5)!=0 ,(mask & 0x62)==0x60)
        elif mode=="inj":
            return np.bitwise_and((mask & 0x7)!=0 ,(mask & 0x180)==0x180)
        else:
            return mask

########################## scans  #############################################

    def get_occupancy(self, exp_time):
        self['data_rx'].set_en(True)
        self.reset_ibias()
        for _ in range(10):
            self['fifo'].reset()
            time.sleep(0.002)
        time.sleep(exp_time)
        dat = self.interpret_data(self['fifo'].get_data())
        print("Number of pixels counted: %d" % len(dat))
        pix_tmp, cnt = np.unique(dat[["col","row"]], return_counts=True)
        arg = np.argsort(cnt)
        print('column, row) hits \n')
        for a_i, a in enumerate(arg[::-1]):
            print pix_tmp[a], cnt[a]
        return pix_tmp, cnt


    def inj_scan_1pix(self, flavor, col, row, VL, VHLrange, start_dif, delay, width, repeat, noise_en, analog_en, sleeptime):

        hits = np.zeros((VHLrange + 1), dtype=int)

        self['inj'].set_delay(delay)
        self['inj'].set_width(width)
        self['inj'].set_repeat(repeat)
        self['inj'].set_en(0)

        self['CONF_SR']['INJ_ROW'].setall(False)
        if analog_en == 1:
            self['CONF_SR']['INJ_ROW'][223] = True
        self['CONF_SR']['COL_PULSE_SEL'].setall(False)
        self.enable_injection(flavor, col, row)
        self.set_vl_dacunits(VL, 0)
        self.set_vh_dacunits(VL + start_dif, 0)
        self.write_conf()

        for _ in range(5):
            _ = self['fifo'].get_data()

        for i in range(VHLrange + 1):
            self.set_vh_dacunits(VL + i + start_dif, 0)
            self.write_conf()

            while not self['inj'].is_ready:
                time.sleep(0.001)
            for _ in range(10):
                self['inj'].is_ready
            self["inj"].start()

            time.sleep(sleeptime)
            x = self['fifo'].get_data()
            ix = self.interpret_data(x)

            cnt = 0
            for hit in ix:
                if hit['col'] == col and hit['row'] == row:
                    if noise_en == 1:
                        if hit['noise'] == 0:
                            cnt += 1
                    else:
                        cnt += 1

            hits[i] = cnt
        return hits

    def auto_mask(self, th=2, step=50, dt=0.2, already_masked=set()):
        """Automatically finds and masks noisy pixels.
        
        `th`: masks the pixels that receive >= this number of hits in `dt`
        `dt`: the time to wait for hits in seconds
        `step`: unmask this number of rows/columns/diagonals at a time
                (useful if there are pixels that fill up the fifo)
        `already_masked`: list of pixels (fl_n, col, row) to be kept masked
        """
        self.mask_all()
        self.enable_data_rx()

        # Set of noisy pixels to fill, as tuples (flavor, col, row)
        noisy_pixels = set(already_masked)

        def find_new_noisy_pixels():
            # Get hits and see which pixels are noisy
            hits, pixels, hits_per_pixel = self.recv_data_summary(dt)
            for px, n_hits in zip(pixels, hits_per_pixel):
                if n_hits >= th:
                    if 0 <= px['col'] <= 111 and 0 <= px['row'] <= 223:
                        noisy_pixels.add((self.fl_n, px["col"], px["row"]))
                    else:  # This happens due to a bug or communication error
                        print("Warning: invalid pixel with col,row = %d,%d" % (px['col'], px['row']))
            print("Got %d hits, total noisy pixels: %d" % (len(hits), len(noisy_pixels)))

        # Iterate over MASKH to find noisy pixels
        for i in np.append(range(step, 223, step), 223):
            # Unmask step rows at a time
            self['CONF_SR']['MASKH'][i:0] = (int(i) + 1) * bitarray('1')
            # Mask noisy pixels that we found before
            for flavor, col, row in noisy_pixels:
                self.mask(flavor, col, row)
            self['CONF_SR'].write()

            print("Enable MASKH %d" % i)
            find_new_noisy_pixels()

        # Iterate over MASKV to find noisy pixels
        for i in np.append(range(step, 111, step), 111):
            # Unmask step columns at a time, while keeping all rows unmasked
            self['CONF_SR']['MASKV'][i + (self.fl_n * 112):(self.fl_n * 112)] = (int(i) + 1) * bitarray('1')
            # Mask noisy pixels that we found before
            for flavor, col, row in noisy_pixels:
                self.mask(flavor, col, row)
            self['CONF_SR'].write()

            print("Enable MASKV %d" % i)
            find_new_noisy_pixels()

        # Iterate over MASKD to find noisy pixels
        for i in np.append(range(step, len(self['CONF_SR']['MASKD']) - 1, step), len(self['CONF_SR']['MASKD']) - 1):
            # Unmask step diagonals at a time, while keeping all rows and cols unmasked
            self['CONF_SR']['MASKD'][i:0] = (int(i)+1)*bitarray('1')
            # Mask noisy pixels that we found before
            for flavor, col, row in noisy_pixels:
                self.mask(flavor, col, row)
            self['CONF_SR'].write()

            print("Enable MASKD %d" % i)
            find_new_noisy_pixels()

        # Mask all previously-found noisy pixels and check again
        for flavor, col, row in noisy_pixels:
            self.mask(flavor, col, row)
        self['CONF_SR'].write()

        print("Checking again after masking")
        find_new_noisy_pixels()

        # Mask additionally found noisy pixels
        for flavor, col, row in noisy_pixels:
            self.mask(flavor, col, row)
        self['CONF_SR'].write()
        time.sleep(0.3)
        self['fifo'].reset()
        self.reset_ibias()

        print("Noisy pixels: %d" % len(noisy_pixels))
        # Get masked pixels using a convenience function of the TJMonopix class
        mask = self.get_disabled_pixel(maskV=self['CONF_SR']['MASKV'], maskH=self['CONF_SR']['MASKH'], maskD=self['CONF_SR']['MASKD'])
        total_enabled = np.shape(np.argwhere(mask[(self.fl_n * 112):(self.fl_n + 1) * 112, :] != 0))[0]
        total_disabled = np.shape(np.argwhere(mask[(self.fl_n * 112):(self.fl_n + 1) * 112, :] == 0))[0]
        print("Enabled pixels: %d" % total_enabled)
        print("Disabled pixels (noisy + unintentionally masked): %d" % total_disabled)
        return noisy_pixels, total_disabled, np.argwhere(mask[(self.fl_n * 112):(self.fl_n + 1) * 112, :] == 0)

    ######## Our utilities #################

    def mask_all(self, unmask=False):
        """Set mask for all pixels"""
        self['CONF_SR'][self.SET['fl']].setall(False)
        self['CONF_SR']['EN_OUT'][self.fl_n] = False
        self['CONF_SR']['MASKD'].setall(unmask)
        self['CONF_SR']['MASKH'].setall(unmask)
        self['CONF_SR']['MASKV'].setall(unmask)
        self.write_conf()

        self['CONF_SR'][self.SET['fl']].setall(True)
        self.write_conf()

    def unmask_all(self):
        """Unmask all pixels"""
        self.mask_all(True)

    def standard_auto_mask(self, th1=1000, th2=10, th3=2):
        """Executes a standard set of auto_mask calls."""
        noisy_pixels, _, _ = self.auto_mask(th=th1, dt=0.02)
        noisy_pixels, _, _ = self.auto_mask(th=th2, dt=0.02, already_masked=noisy_pixels)
        noisy_pixels, total_disabled, mask = self.auto_mask(th=th3, step=100, dt=0.2, already_masked=noisy_pixels)
        return noisy_pixels, total_disabled, mask

    def enable_data_rx(self, wait=0.1):
        """Enable data rx FIFO"""
        self['data_rx'].set_en(True)
        for _ in range(10):
            self["fifo"].reset()
            time.sleep(wait)

    def recv_data(self, dt=0.2, wait_inj=False):
        """Receive and parse data"""
        self.reset_ibias()  # Reset Ibias and wait for oscillations to stabilize
        self.reset_ibias()  # Oscillations may arise from configuration changes
        self['fifo'].reset()  # Clear the buffer
        if wait_inj:
            self["inj"].start()
            while not self['inj'].is_ready:
                time.sleep(0.001)
        time.sleep(dt)  # Wait integration time
        return self.interpret_data(self['fifo'].get_data())  # Return array of hits

    def recv_data_summary(self, dt=0.2, wait_inj=False):
        """Same as above, but also return array of pixels with hits and number of hits per pixel"""
        hits = self.recv_data(dt, wait_inj)
        pixels, hits_per_pixel = np.unique(hits[["col", "row"]], return_counts=True)
        return hits, pixels, hits_per_pixel


    def injection_scan(self, injlist, inj_low_dac, col_to_inject, row_to_inject):
        self['data_rx'].set_en(True)
        for _ in range(5):
            self['fifo'].reset()
            time.sleep(0.002)
        time.sleep(2)

        cnt = np.empty(len(injlist))
        tot = np.empty(len(injlist))
        inj_high = np.empty(len(injlist))

        print "inj[dac] inj[V] len(ix), len(ix_inj) aveToT"
        for inj_i, inj in enumerate(injlist):
            inj_high_dac = inj + inj_low_dac
            inj_high_pulse = self.set_vh_dacunits(inj_high_dac, 0)
            self.write_conf()
            for _ in range(5):
                self['fifo'].reset()
                time.sleep(0.002)
            self.set_monoread()
            self["inj"].start()
            while not self['inj'].is_ready:
                time.sleep(0.001)
            time.sleep(0.02)

            ix = self.interpret_data(self['fifo'].get_data())
            ix_inj = ix[np.bitwise_and(ix["col"] == col_to_inject, ix["row"] == row_to_inject)]
            cnt[inj_i] = len(ix_inj)
            tot[inj_i] = np.average((ix_inj["te"]-ix_inj["le"]) & 0x3F)
            inj_high[inj_i] = inj_high_pulse
            print inj, inj_high_pulse, len(ix), len(ix_inj), tot[inj_i]
        return cnt, tot, inj_high




    def select_injection(self, col_to_inject, row_to_inject = None):
        """Select the pixel or the column to inject """
        self['CONF_SR']['INJ_ROW'].setall(False)
        self['CONF_SR']['COL_PULSE_SEL'].setall(False)

        if row_to_inject == None:
            self['CONF_SR']['INJ_ROW'].setall(True)
            self['CONF_SR']['COL_PULSE_SEL'][(3 * 112) + col_to_inject] = True
            print("col injected: ", col_to_inject)

        else:
            self.enable_injection(3, col_to_inject, row_to_inject)
            print("pixel (col and row) injected", col_to_inject, row_to_inject)
        self.write_conf()
        return


class FakeTJMonoPix(TJMonoPix):
    """A minimal simulation of a monopix to test scripts before going to lab."""
    class ConfDict(defaultdict):
        def __init__(self, *args, **kwargs):
            super(FakeTJMonoPix.ConfDict, self).__init__(FakeTJMonoPix.ConfDict)
            self["all"] = 0
            self[0] = 0
            for i, arg in enumerate(args):
                self[i] = arg
            self.update(kwargs)
            self.last_reset = time.time()

        def write(self):
            pass

        def reset(self):
            self.last_reset = time.time()

        def read(self, *args, **kwargs):
            return 0

        def start(self):
            pass

        def setall(self, value):
            self["all"] = int(value)

        def get_data(self):
            n = int(min(1000000, 1000 * (time.time() - self.last_reset)))
            self.last_reset = time.time()
            col = np.random.randint(112, size=n)
            row = np.random.randint(224, size=n)
            le = np.random.randint(64, size=n)
            te = np.random.randint(64, size=n)
            res = np.zeros((n,), FakeTJMonoPix.HIT_DTYPE)
            res["col"] = col
            res["row"] = row
            res["le"] = le
            res["te"] = te
            return res

        @property
        def is_ready(self):
            return True

        def __getattr__(self, attr):
            if attr.startswith("set_"):
                def method(*args, **kwargs):
                    self[attr[4:]] = FakeTJMonoPix.ConfDict(*args, **kwargs)
            elif attr.startswith("get_"):
                def method(*args, **kwargs):
                    try:
                        return self[attr[4:]][0]
                    except Exception:
                        return self[attr[4:]]
            else:
                def method(*args, **kwargs):
                    print("DEBUG %s called" % attr)
            return method

        def __getitem__(self, key):
            if isinstance(key, slice):
                res = []
                start = int(key.start or 0)
                stop = int(key.stop or 0)
                step = int(key.step or 1)
                for i in range(start, stop, abs(step) * (-1 if start > stop else 1)):
                    if i not in self:
                        super(FakeTJMonoPix.ConfDict, self).__setitem__(i, self["all"])
                    res.append(self[i])
                return res
            if isinstance(key, int):
                if key not in self:
                    super(FakeTJMonoPix.ConfDict, self).__setitem__(key, self["all"])
            return super(FakeTJMonoPix.ConfDict, self).__getitem__(key)

        def __setitem__(self, key, value):
            if isinstance(key, slice):
                start = int(key.start or 0)
                stop = int(key.stop or 0)
                step = int(key.step or 1)
                for vi, i in enumerate(range(start, stop, abs(step) * (-1 if start > stop else 1))):
                    super(FakeTJMonoPix.ConfDict, self).__setitem__(i, int(value[vi]))
            elif isinstance(key, int):
                super(FakeTJMonoPix.ConfDict, self).__setitem__(key, int(value))
            else:
                super(FakeTJMonoPix.ConfDict, self).__setitem__(key, value)

    HIT_DTYPE = np.dtype([("col", "<u1"), ("row", "<u2"), ("le", "<u1"), ("te", "<u1"), ("noise", "<u1")])

    def __init__(self, conf=None, no_power_reset=False):
        # No call to super().__init__ !
        self.SET = {'VDDA': None, 'VDDP': None, 'VDDA_DAC': None, 'VDDD': None,
                    'VPCSWSF': None, 'VPC': None, 'BiasSF': None, 'INJ_LO': None, 'INJ_HI': None,
                    'DACMON_ICASN': None, 'fl': None}
        self.SET["conf"] = conf
        self.SET["no_power_reset"] = no_power_reset
        self.ROW = 224
        self.COL = 112
        self.debug = 0
        self.conf_flg = 1
        self._conf = FakeTJMonoPix.ConfDict()
        self._conf["name"] = "FakeTJMonoPix"
        self._conf["version"] = 0
        self.name = "FakeTJMonoPix"
        self.version = 0
        self._registers = FakeTJMonoPix.ConfDict()
        self._initialized = False
        self.conf_path = None
        self.parent = None

    def init(self, fl="EN_PMOS"):
        self['CONF']['DEF_CONF_N'] = 0
        self.switch_flavor(fl)
        self.power_on()
        self['CONF']['RESET_BCID'] = 1
        self['CONF']['RESET'] = 1
        self['CONF'].write()
        self['CONF']['EN_BX_CLK'] = 1
        self['CONF']['EN_OUT_CLK'] = 1
        self['CONF'].write()
        self['CONF']['RESET_BCID'] = 0
        self['CONF']['RESET'] = 0
        self['CONF'].write()
        self.default_conf()
        self.write_conf()
        self['CONF']['DEF_CONF_N'] = 1
        self['CONF'].write()

    def write_conf(self):
        pass

    def get_configuration(self):
        res = dict(self._conf)
        res.update(self._registers)
        return res

    def interpret_data(self, raw_data):
        if raw_data.dtype == FakeTJMonoPix.HIT_DTYPE:
            return raw_data
        return super(FakeTJMonoPix, self).interpret_data(raw_data)

    def __getitem__(self, key):
        return self._registers[key]

    def __iter__(self):
        return iter(self._registers)

    def __setitem__(self, key, value):
        self._registers[key] = value

    def __repr__(self):
        return "FakeTJMonoPix(%s)" % self.get_configuration()


if __name__ == '__main__':
    chip = TJMonoPix()
    chip.init()
