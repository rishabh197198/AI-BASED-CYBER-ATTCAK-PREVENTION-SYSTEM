import React, { useEffect, useState } from 'react';
import ThreatCard from '../components/ThreatCard';
import AttackGraph from '../components/AttackGraph';

const Dashboard = () => {

    const [stats, setStats] = useState(null);

    useEffect(() => {
        fetch("http://127.0.0.1:8000/api/stats/")
            .then(res => res.json())
            .then(data => {
                setStats(data);
            })
            .catch(err => console.log(err));
    }, []);

    return (
        <div className="p-8">
            {/* Page Header */}
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-white">System Overview</h1>
                <p className="text-slate-400 font-medium">AI-driven real-time threat monitoring</p>
            </header>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <ThreatCard 
                    title="Active Threats" 
                    value={stats ? stats.active_threats : "Loading..."} 
                    status="safe" 
                />
                <ThreatCard 
                    title="Packets Scanned (24h)" 
                    value={stats ? stats.packets_scanned : "Loading..."} 
                    status="safe" 
                />
                <ThreatCard 
                    title="Last Attack Prevented" 
                    value={stats ? stats.last_attack : "Loading..."} 
                    status="danger" 
                />
            </div>

            {/* Live Traffic Section */}
            <div className="mb-8">
                <AttackGraph />
            </div>

            <div className="p-8 h-80 flex flex-col items-center justify-center">
                <div className="w-full max-w-2xl h-48 flex items-end justify-between space-x-2">
                    {[40, 70, 45, 90, 65, 80, 30, 55, 95, 40].map((h, i) => (
                        <div
                            key={i}
                            className="bg-emerald-500 w-full"
                            style={{ height: `${h}%` }}
                        ></div>
                    ))}
                </div>
                <p className="mt-6 text-slate-500 text-sm font-mono tracking-wider">
                    ENCRYPTION ENGINE ACTIVE: MONITORING PORT 443
                </p>
            </div>
        </div>
    );
};

export default Dashboard;