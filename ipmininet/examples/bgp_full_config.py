from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, BGP, ebgp_session, set_local_pref, set_med, set_rr, new_access_list, set_community, new_community_list, AF_INET6


class BGPTopoFull(IPTopo):
	"""This topology is composed of two AS connected in dual homing with different local pref"""
	def build(self, *args, **kwargs):
		"""
	TODO
		   +----------+                                   +--------+
					  |                                   |
		 AS1          |                  AS2              |        AS3
					  |                                   |
					  |                                   |
	+-------+   eBGP  |  +-------+     iBGP    +-------+  |  eBGP   +-------+
	| as1r1 +------------+ as2r1 +-------------+ as2r2 +------------+ as3r1 |
	+-------+         |  +-------+             +-------+  |         +-------+
					  |                                   |
					  |                                   |
					  |                                   |
		 +------------+                                   +--------+
		"""
		# Add all routers
		as1r1 = self.addRouter('as1r1')
		as1r1.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
		as1r2 = self.addRouter('as1r2')
		as1r2.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
		as1r3 = self.addRouter('as1r3')
		as1r3.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
		as1r4 = self.addRouter('as1r4')
		as1r4.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
		as1r5 = self.addRouter('as1r5')
		as1r5.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
		as1r6 = self.addRouter('as1r6')
		as1r6.addDaemon(BGP, address_families=(
            AF_INET6(redistribute=('connected',)),))
		as4r1 = self.addRouter('as4r1')
		as4r1.addDaemon(BGP, address_families=(AF_INET6(networks=('dead:beef::/32',)),))
		as4r2 = self.addRouter('as4r2')
		as4r2.addDaemon(BGP, address_families=(AF_INET6(networks=('dead:beef::/32',)),))
		as4h1 = self.addHost("as4h1")

		# Add Links
		self.addLink(as1r1, as1r6, params1={"ip": ("fd00:1:1::1/48",)},
					 params2={"ip": ("fd00:1:1::2/48",)})
		self.addLink(as1r1, as1r3, params1={"ip": ("fd00:1:2::1/48",)},
					 params2={"ip": ("fd00:1:2::2/48",)})
		self.addLink(as1r3, as1r2, params1={"ip": ("fd00:3:1::1/48",)},
					 params2={"ip": ("fd00:3:1::2/48",)})
		self.addLink(as1r3, as1r6, params1={"ip": ("fd00:3:2::1/48",)},
					 params2={"ip": ("fd00:3:2::2/48",)})
		self.addLink(as1r2, as1r4, params1={"ip": ("fd00:4:1::1/48",)},
					 params2={"ip": ("fd00:4:1::2/48",)})
		self.addLink(as1r4, as1r5, params1={"ip": ("fd00:4:2::1/48",)},
					 params2={"ip": ("fd00:4:2::2/48",)})
		self.addLink(as1r5, as1r6, params1={"ip": ("fd00:5:1::1/48",)},
					 params2={"ip": ("fd00:5:1::2/48",)})
		self.addLink(as4r1, as1r6, params1={"ip": ("fd00:6:1::1/48",)},
					 params2={"ip": ("fd00:6:1::2/48",)})
		self.addLink(as4r2, as1r5, params1={"ip": ("fd00:5:2::1/48",)},
					 params2={"ip": ("fd00:5:2::2/48",)})
		self.addLink(as4r1, as4h1, params1={"ip": ("dead:beef::1/32",)},
					 params2={"ip": ("dead:beef::2/32",)})
		self.addLink(as4r2, as4h1, params1={"ip": ("dead:beef::2/32",)},
					 params2={"ip": ("dead:beef::1/32",)})


		new_access_list(self, (as1r6, as1r5, as4r1, as4r2), 'all', ('any',))
		new_community_list(self, (as1r6,), 'loc-pref', '1:80')
		set_local_pref(self, as1r6, as4r1, 99, filter_type='community', filter_names=('loc-pref',))
		set_community(self, as4r1, as1r6, '1:80', filter_type='access-list', filter_names=('all',))
		set_med(self, as1r6, as4r1, 50, filter_type='access-list', filter_names=('all',))
		set_med(self, as4r1, as1r6, 50, filter_type='access-list', filter_names=('all',))
		set_local_pref(self, as1r5, as4r2, 50, filter_type='access-list', filter_names=('all',))

		# Add full mesh
		self.addAS(4, (as4r1, as4r2))
		self.addAS(1, (as1r1, as1r2, as1r3, as1r4, as1r5, as1r6))
		set_rr(self, as1r3, (as1r1, as1r2, as1r4, as1r5, as1r6))
		# self.addiBGPFullMesh(1, (as1r1, as1r2, as1r3, as1r4, as1r5, as1r6))

		# Add eBGP session
		ebgp_session(self, as1r6, as4r1)
		ebgp_session(self, as1r5, as4r2)


		# Add test hosts ?
		# for r in self.routers():
		#     self.addLink(r, self.addHost('h%s' % r))
		super(BGPTopoFull, self).build(*args, **kwargs)

	def bgp(self, name):
		r = self.addRouter(name, config=RouterConfig)
		r.addDaemon(BGP, address_families=(
			_bgp.AF_INET(redistribute=('connected',)),
			_bgp.AF_INET6(redistribute=('connected',))))
		return r
