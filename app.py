<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UTE_WEB | Supermax Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .stat-card { background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%); border: 1px solid rgba(255, 255, 255, 0.05); }
    </style>
</head>
<body class="bg-[#020617] text-slate-300 min-h-screen font-['Inter',sans-serif]">

    <div class="flex">
        <aside class="w-72 min-h-screen glass p-8 hidden lg:block border-r border-white/5">
            <div class="flex items-center space-x-3 mb-12">
                <div class="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
                    <i class="fa fa-bolt text-white"></i>
                </div>
                <h1 class="text-2xl font-black text-white tracking-tighter italic">UTE_WEB</h1>
            </div>
            
            <nav class="space-y-6">
                <div class="text-xs font-bold text-slate-500 uppercase tracking-widest">Main Menu</div>
                <a href="/" class="flex items-center space-x-4 text-blue-400 font-bold"><i class="fa fa-th-large"></i> <span>Overview</span></a>
                <a href="#" class="flex items-center space-x-4 hover:text-white transition"><i class="fa fa-wallet"></i> <span>Wallet</span></a>
                <a href="#" class="flex items-center space-x-4 hover:text-white transition"><i class="fa fa-history"></i> <span>Activity</span></a>
                <div class="pt-10">
                    <a href="/logout" class="flex items-center space-x-4 text-red-500 hover:text-red-400"><i class="fa fa-power-off"></i> <span>Sign Out</span></a>
                </div>
            </nav>
        </aside>

        <main class="flex-1 p-6 lg:p-12">
            <header class="flex flex-col md:flex-row justify-between items-start md:items-center mb-12 gap-6">
                <div>
                    <p class="text-blue-500 font-bold tracking-widest text-xs uppercase mb-1">Supermax Enterprise</p>
                    <h2 class="text-4xl font-black text-white">Console</h2>
                </div>
                <div class="flex items-center space-x-6 bg-white/5 p-4 rounded-3xl border border-white/5">
                    <div class="text-right">
                        <p class="text-xs text-slate-500 font-bold uppercase">Available Funds</p>
                        <p class="text-2xl font-black text-green-400">KES {{ "{:,.2f}".format(balance) }}</p>
                    </div>
                    <div class="w-12 h-12 bg-green-500/20 rounded-2xl flex items-center justify-center text-green-500">
                        <i class="fa fa-arrow-up"></i>
                    </div>
                </div>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <div class="stat-card p-6 rounded-3xl">
                    <p class="text-slate-500 text-sm mb-1">Total Network Users</p>
                    <p class="text-3xl font-bold text-white">{{ stats.total_users }}</p>
                </div>
                <div class="stat-card p-6 rounded-3xl">
                    <p class="text-slate-500 text-sm mb-1">Open Opportunities</p>
                    <p class="text-3xl font-bold text-white">{{ stats.active_jobs }}</p>
                </div>
                <div class="stat-card p-6 rounded-3xl border-l-4 border-blue-600">
                    <p class="text-blue-500 text-sm font-bold mb-1">Platform Stability</p>
                    <p class="text-3xl font-bold text-white">99.9%</p>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
                <section class="glass rounded-[2.5rem] p-8">
                    <h3 class="text-xl font-bold mb-6 flex items-center space-x-3">
                        <span class="w-2 h-6 bg-blue-600 rounded-full"></span>
                        <span>Active Payrolls</span>
                    </h3>
                    <div class="space-y-4">
                        {% for c in contracts %}
                        <div class="bg-white/5 p-5 rounded-2xl flex justify-between items-center border border-white/5">
                            <div>
                                <p class="font-bold text-white">{{ c.employee if user.role != 'employee' else c.employer }}</p>
                                <p class="text-xs text-slate-500">Monthly: KES {{ "{:,.2f}".format(c.salary) }}</p>
                            </div>
                            {% if user.role != 'employee' %}
                            <button onclick="payStaff({{ c.id }})" class="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-xl text-sm font-bold transition">EXECUTE PAY</button>
                            {% else %}
                            <div class="text-right">
                                <p class="text-xs text-slate-500">Payments</p>
                                <p class="font-bold text-blue-400">{{ c.total_months_paid }}</p>
                            </div>
                            {% endif %}
                        </div>
                        {% endfor %}
                    </div>
                </section>

                <section class="glass rounded-[2.5rem] p-8">
                    <div class="flex justify-between items-center mb-6">
                        <h3 class="text-xl font-bold">Marketplace</h3>
                        {% if user.role != 'employee' %}
                        <button onclick="showJobModal()" class="text-blue-400 font-bold text-sm hover:underline">+ New Entry</button>
                        {% endif %}
                    </div>
                    <div class="space-y-4">
                        {% for job in jobs %}
                        <div class="flex items-center justify-between p-4 hover:bg-white/5 rounded-2xl transition group">
                            <div class="flex items-center space-x-4">
                                <div class="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center group-hover:bg-blue-600 transition">
                                    <i class="fa fa-briefcase text-xs"></i>
                                </div>
                                <div>
                                    <p class="font-bold text-white text-sm">{{ job.title }}</p>
                                    <p class="text-xs text-slate-500">{{ job.employer }}</p>
                                </div>
                            </div>
                            {% if user.role == 'employee' %}
                            <form action="/apply/{{ job.id }}" method="POST">
                                <button class="text-xs font-bold text-blue-400 border border-blue-400/30 px-4 py-2 rounded-lg hover:bg-blue-400 hover:text-white transition">APPLY</button>
                            </form>
                            {% endif %}
                        </div>
                        {% endfor %}
                    </div>
                </section>
            </div>
        </main>
    </div>

    <script>
    function payStaff(id) {
        const btn = event.target;
        btn.innerHTML = "<i class='fa fa-spinner fa-spin'></i>";
        fetch(`/pay_contract/${id}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if(data.error) alert(data.error);
            else alert("M-Pesa Signal Dispatched!");
            location.reload();
        });
    }
    </script>
</body>
</html>
