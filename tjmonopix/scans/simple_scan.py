import time
import yaml
from tqdm import tqdm

from tjmonopix.scan_base import ScanBase
import tjmonopix.analysis.interpreter_idx as interpreter_idx
from tjmonopix.analysis import plotting


class SimpleScan(ScanBase):
    scan_id = "simple"

    def scan(self, **kwargs):
        with_tj = kwargs.pop('with_tj', True)
        with_tlu = kwargs.pop('with_tlu', True)
        with_timestamp = kwargs.pop('with_timestamp', True)
        with_tdc = kwargs.pop('with_tdc', True)
        scan_timeout = kwargs.pop('scan_timeout', 10)

        cnt = 0
        scanned = 0

        # Stop readout and clean FIFO
        self.dut.stop_all()
        self.dut['fifo'].reset()

        # Start readout
        if with_tj:
            self.dut.set_monoread()
        for _ in range(5):  # Reset FIFO to clean up
            time.sleep(0.05)
            self.dut['fifo'].reset()
        if with_tdc:
            self.dut.set_timestamp("mon")
        if with_tlu:
            tlu_delay = kwargs.pop('tlu_delay', 8)
            self.dut.set_tlu(tlu_delay)
        if with_timestamp:
            self.dut.set_timestamp("rx1")

        self.dut.reset_ibias()

        # Start FIFO readout
        pbar = tqdm(total=scan_timeout, unit="s", unit_scale=True, bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{postfix}]')
        with self.readout(scan_param_id=0, fill_buffer=False, clear_buffer=True, readout_interval=0.2, timeout=0):
            self.dut.reset_ibias()

            t0 = time.time()

            self.logger.info(
                "*****{} is running **** don't forget to start tlu ****".format(self.__class__.__name__))
            while True:
                pre_cnt = cnt
                cnt = self.fifo_readout.get_record_count()
                pre_scanned = scanned
                scanned = time.time() - t0
                temp = self.dut.get_temperature()

                pbar.set_postfix(ordered_dict={'Data Rate': '{:.3f} k/s'.format((cnt - pre_cnt) / max(1e-3, scanned - pre_scanned) / 1024), 'Temp': '{:5.1f} C'.format(temp)})
                pbar.update(scanned - pre_scanned)
                if scanned + 2 > scan_timeout and scan_timeout > 0:
                    break
                time.sleep(1)
            time.sleep(max(0, scan_timeout - scanned))
        pbar.close()

        # Stop FIFO readout
        if with_timestamp:
            self.dut.stop_all()
            self.meta_data_table.attrs.timestamp_status = yaml.dump(
                self.dut["timestamp_rx1"].get_configuration())
        if with_tlu:
            self.dut.stop_tlu()
            self.meta_data_table.attrs.tlu_status = yaml.dump(
                self.dut["tlu"].get_configuration())
        if with_tdc:
            self.dut.stop_tdc()
        if with_tj:
            self.dut.stop_monoread()

    @classmethod
    def analyze(self, data_file=None, cluster_hits=False):
        if data_file is None:
            data_file = self.output_filename + '.h5'
        out_file = data_file[:-3] + "_interpreted.h5"

        interpreter_idx.interpret_idx_h5(data_file, out_file)
        return out_file

    @classmethod
    def plot(self, analyzed_data_file=None):
        if analyzed_data_file is None:
            analyzed_data_file = self.analyzed_data_file
        with plotting.Plotting(analyzed_data_file=analyzed_data_file) as p:
            p.create_standard_plots()


if __name__ == "__main__":
    scan = SimpleScan()
    scan.scan()
    scan.analyze()
