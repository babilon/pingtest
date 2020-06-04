import subprocess
import sys
import datetime

write=False
filename='log.txt' # log file

count = 0 # 0 for indefinite; > 0 for specific number
interval = 3 # time in seconds between pings
ipaddr = 'google.com' # ip address or domain name
print_after = 5 # number of pings between prints/dump to log file
ipv4 = False
ipv6 = False

buckets = (20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250, 300, 400, 500,
750, 1000, 1200, 1300, 1400, 1500, 2000)
bucket_counters = [0 for n in range(len(buckets))]

starttime = None

def dump_to_file(s, f):
        sys.stdout.write(s)
        f.write(s)

def dump_bucket_counters(sequence):
    with open(filename, 'w') as f:
        currenttime = datetime.datetime.now()
        delta = currenttime - starttime
        dump_to_file("Calculated time: %14s %s\n" %
                (str(datetime.timedelta(seconds=sequence *
                interval)),
                ipaddr), f)
        dump_to_file('Total: %10d %20s\n' % (sequence, str(delta)), f)
        dump_to_file('_' * 80 + '\n', f)
        for x in range(len(buckets)):
            if bucket_counters[x] > 0:
                dump_to_file("%5d: %10d\n" % (buckets[x],
                        bucket_counters[x]),
                        f)
        dump_to_file('_' * 80 + '\n', f)

def execute(command):
    global starttime
    starttime = datetime.datetime.now() 
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    processed = 0

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if len(nextline) == 0 and process.poll() is not None:
            break

        if nextline.decode('utf-8').startswith('64 bytes'):
            s = nextline.decode('utf-8')
            if write:
                sys.stdout.write(s)
                sys.stdout.flush()
            significant = s.split(' ')
            sequence = 0
            time = 0
            for p in significant:
                if p.startswith('icmp_seq='):
                    sequence = int(p.split('=')[-1])
                elif p.startswith('time='):
                    time = p.split('=')[-1]
            #print(time)
            time = float(time)
            for x in range(len(buckets)):
                if time <= buckets[x]:
                    bucket_counters[x] += 1
                    break

            processed += 1

            if processed >= print_after:
                dump_bucket_counters(sequence)
                processed = 0

    if processed > 0:
        dump_bucket_counters(sequence)

    output = process.communicate()[0]
    exitCode = process.returncode

    if exitCode == 0:
        return output
    else:
        sys.stderr.write("exit with code %d\n" % exitCode)
        return output


def form_cmd(count=0, interval=3, ipaddr="ddg.gg"):
    cmd = 'ping '
    cnt = ('-c %d ' % count) if count > 0 else ''
    interval = ('-i %d ' % interval) if interval > 0 else ''
    cmd += cnt + ('-4 ' if ipv4 else ('-6 ' if ipv6 else '')) + interval + ipaddr.strip()
    return cmd


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='IP or Domain to ping.')
    parser.add_argument('ipaddr', metavar='ipaddr', type=str, nargs=1,
        help='IP address or domain to ping')
    parser.add_argument('filename', metavar='log', type=str, nargs=1,
        help='Log file to dump latest data to')
    parser.add_argument('-i', dest='interval', action='store', type=int,
        default=3,
        help='Interval in seconds between pings; minimum is 1 second')
    parser.add_argument('-c', dest='count', action='store', type=int,
        default=5,
        help='Number of pings; A value of 0 means indefinite.')
    parser.add_argument('-H', dest='hours', action='store', type=int,
        default=0,
        help='Number of hours to ping. Non-zero computes a value for -c based \
        on interval and invokes ping -c N')
    parser.add_argument('-p', dest='print_after', action='store', type=int,
        default=5,
        help='Number of pings to issue befer dumping latest stats to log')
    parser.add_argument('-w', dest='write', action='store_true',
        default=False,
        help='Flag when set to true dumps ping output to stdout')
    parser.add_argument('-4', dest='ipv4', action='store_true',
        default=False,
        help='Enable IPv4 only mode')
    parser.add_argument('-6', dest='ipv6', action='store_true',
        default=False,
        help='Enable IPv6 only mode')
    args = parser.parse_args()
    interval = args.interval
    if interval < 1:
        interval = 1

    count = args.count
    hours = args.hours
    if hours > 0:
        count = int(hours * (60.0 * 60.0) / interval)
        print("Invoking 'ping' command %d times for approx. %d hours" %
                (count, hours))

    filename = args.filename[0]
    ipaddr = args.ipaddr[0]
    write = args.write
    print_after = args.print_after
    ipv4 = args.ipv4
    ipv6 = args.ipv6

    execute(form_cmd(count, interval, ipaddr))
