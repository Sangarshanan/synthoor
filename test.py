from synthoor import GatedSound, Envelope, Oscillator, LatencyGate, ResonantFilter

class TB303(GatedSound):

    def __init__(self):

        super().__init__()
        self.shape = 'sawtooth'
        self.resonance = 2
        self.decay = 1

        self.env0 = Envelope(0.2, 0., 1, 0.5)
        self.env1 = Envelope(0., 1., 0., 0., linear=False)

        self.osc0 = Oscillator('sawtooth')
        
        self.filter = ResonantFilter(btype='lowpass', resonance=2)

    def forward(self):
        g0 = self.gate()
        e0 = self.env0(g0)
        
        e1 = self.env1(g0, decay=self.decay) * 10 * 8
        a0 = self.osc0(shape=self.shape, freq=self.freq)

#         a1 = self.filter(
#             a0,
#             resonance=self.resonance,
#             freq=self.freq
#         )
        return a0 * e0


t = TB303()
t.play(duration = 0.2)