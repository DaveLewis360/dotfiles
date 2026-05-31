pragma Singleton

import qs.config
import Quickshell
import Quickshell.Io
import QtQuick

Singleton {
    id: root

    property real cpuPerc
    property real cpuTemp
    readonly property string gpuType: Config.services.gpuType.toUpperCase() || autoGpuType
    property string autoGpuType: "NONE"
    property real gpuPerc
    property real gpuTemp
    property real memUsed
    property real memTotal
    readonly property real memPerc: memTotal > 0 ? memUsed / memTotal : 0
    property real storageUsed
    property real storageTotal
    property real storagePerc: storageTotal > 0 ? storageUsed / storageTotal : 0
    property var disks: []
    property string cpuName: ""
    property string gpuName: ""

    property real lastCpuIdle
    property real lastCpuTotal

    property int refCount

    function formatKib(kib: real) {
        const mib = 1024;
        const gib = 1024 ** 2;
        const tib = 1024 ** 3;

        if (kib >= tib)
            return {
                value: kib / tib,
                unit: "TiB"
            };
        if (kib >= gib)
            return {
                value: kib / gib,
                unit: "GiB"
            };
        if (kib >= mib)
            return {
                value: kib / mib,
                unit: "MiB"
            };
        return {
            value: kib,
            unit: "KiB"
        };
    }

    Timer {
        running: root.refCount > 0
        interval: 3000
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            stat.reload();
            cpuinfo.reload();
            meminfo.reload();
            storage.running = true;
            gpuUsage.running = true;
            sensors.running = true;
        }
    }

    FileView {
        id: stat

        path: "/proc/stat"
        onLoaded: {
            const content = text();
            if (!content) return;
            const match = content.match(/^cpu\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)/);
            if (match) {
                const stats = match.slice(1).map(function(n) { return parseInt(n, 10) || 0; });
                if (stats.length >= 4) {
                    const total = stats.reduce(function(a, b) { return a + b; }, 0);
                    const idle = stats[3] + (stats[4] || 0);

                    const totalDiff = total - root.lastCpuTotal;
                    const idleDiff = idle - root.lastCpuIdle;
                    
                    if (totalDiff > 0)
                        root.cpuPerc = 1 - idleDiff / totalDiff;
                    else
                        root.cpuPerc = 0;

                    root.lastCpuTotal = total;
                    root.lastCpuIdle = idle;
                }
            }
        }
    }

    FileView {
        id: cpuinfo

        path: "/proc/cpuinfo"
        onLoaded: {
            const content = text();
            if (!content) return;
            const match = content.match(/model name\s+:\s+(.*)/);
            if (match && match.length >= 2)
                root.cpuName = match[1].trim();
        }
    }

    FileView {
        id: meminfo

        path: "/proc/meminfo"
        onLoaded: {
            const data = text();
            if (!data) return;
            const totalMatch = data.match(/MemTotal: *(\d+)/);
            const availMatch = data.match(/MemAvailable: *(\d+)/);
            
            root.memTotal = totalMatch ? (parseInt(totalMatch[1], 10) || 1) : 1;
            root.memUsed = availMatch ? (root.memTotal - (parseInt(availMatch[1], 10) || 0)) : 0;
        }
    }

    Process {
        id: storage

        command: ["sh", "-c", "df -kP | grep '^/dev/' | awk '{print $1, $3, $4, $6}'"]
        stdout: StdioCollector {
            onStreamFinished: {
                const deviceMap = {};
                const newDisks = [];

                if (!text || text.trim() === "") {
                    root.disks = [];
                    return;
                }

                const lines = text.trim().split("\n");
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i].trim();
                    if (line === "")
                        continue;

                    const parts = line.split(/\s+/);
                    if (parts.length >= 4) {
                        const device = parts[0];
                        const used = parseInt(parts[1], 10) || 0;
                        const avail = parseInt(parts[2], 10) || 0;
                        const mount = parts[3];

                        const total = used + avail;
                        if (!deviceMap[device] || total > (deviceMap[device].used + deviceMap[device].avail)) {
                            deviceMap[device] = {
                                mount: mount,
                                used: used,
                                avail: avail,
                                total: total,
                                perc: total > 0 ? used / total : 0
                            };
                        }
                    }
                }

                let totalUsed = 0;
                let totalAvail = 0;
                const keys = Object.keys(deviceMap);
                for (let j = 0; j < keys.length; j++) {
                    const stats = deviceMap[keys[j]];
                    totalUsed += stats.used;
                    totalAvail += stats.avail;
                    newDisks.push(stats);
                }

                root.storageUsed = totalUsed;
                root.storageTotal = totalUsed + totalAvail;
                root.disks = newDisks;
            }
        }
    }

    Process {
        id: gpuTypeCheck

        running: !Config.services.gpuType
        command: ["sh", "-c", "if command -v nvidia-smi &>/dev/null && nvidia-smi -L &>/dev/null; then echo NVIDIA && nvidia-smi --query-gpu=name --format=csv,noheader; elif ls /sys/class/drm/card*/device/gpu_busy_percent 2>/dev/null | grep -q .; then echo GENERIC && grep -h . /sys/class/drm/card*/device/model 2>/dev/null || echo GPU; else echo NONE; fi"]
        stdout: StdioCollector {
            onStreamFinished: {
                if (!text || text.trim() === "")
                    return;

                const lines = text.trim().split("\n");
                if (lines.length >= 1) {
                    root.autoGpuType = lines[0].trim();
                }
                if (lines.length >= 2) {
                    root.gpuName = lines[1].trim();
                } else if (root.autoGpuType === "GENERIC") {
                    root.gpuName = "Generic GPU";
                }
            }
        }
    }

    Process {
        id: gpuUsage

        command: root.gpuType === "GENERIC" ? ["sh", "-c", "cat /sys/class/drm/card*/device/gpu_busy_percent"] : root.gpuType === "NVIDIA" ? ["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"] : ["echo"]
        stdout: StdioCollector {
            onStreamFinished: {
                if (root.gpuType === "GENERIC") {
                    if (!text || text.trim() === "") {
                        root.gpuPerc = 0;
                        return;
                    }
                    const percs = text.trim().split("\n");
                    const sum = percs.reduce((acc, d) => acc + parseInt(d, 10), 0);
                    root.gpuPerc = sum / percs.length / 100;
                } else if (root.gpuType === "NVIDIA") {
                    if (!text || text.trim() === "") {
                        root.gpuPerc = 0;
                        root.gpuTemp = 0;
                        return;
                    }
                    const parts = text.trim().split(",");
                    if (parts.length >= 2) {
                        root.gpuPerc = parseInt(parts[0], 10) / 100;
                        root.gpuTemp = parseInt(parts[1], 10);
                    }
                } else {
                    root.gpuPerc = 0;
                    root.gpuTemp = 0;
                }
            }
        }
    }

    Process {
        id: sensors

        command: ["sensors"]
        environment: ({
                LANG: "C.UTF-8",
                LC_ALL: "C.UTF-8"
            })
        stdout: StdioCollector {
            onStreamFinished: {
                let cpuTemp = text.match(/(?:Package id [0-9]+|Tdie):\s+((\+|-)[0-9.]+)(°| )C/);
                if (!cpuTemp)
                    // If AMD Tdie pattern failed, try fallback on Tctl
                    cpuTemp = text.match(/Tctl:\s+((\+|-)[0-9.]+)(°| )C/);

                if (cpuTemp)
                    root.cpuTemp = parseFloat(cpuTemp[1]);

                if (root.gpuType !== "GENERIC")
                    return;

                let eligible = false;
                let sum = 0;
                let count = 0;

                for (const line of text.trim().split("\n")) {
                    if (line === "Adapter: PCI adapter")
                        eligible = true;
                    else if (line === "")
                        eligible = false;
                    else if (eligible) {
                        let match = line.match(/^(temp[0-9]+|GPU core|edge)+:\s+\+([0-9]+\.[0-9]+)(°| )C/);
                        if (!match)
                            // Fall back to junction/mem if GPU doesn't have edge temp (for AMD GPUs)
                            match = line.match(/^(junction|mem)+:\s+\+([0-9]+\.[0-9]+)(°| )C/);

                        if (match) {
                            sum += parseFloat(match[2]);
                            count++;
                        }
                    }
                }

                root.gpuTemp = count > 0 ? sum / count : 0;
            }
        }
    }
}
