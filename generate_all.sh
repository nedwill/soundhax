#!/bin/bash

# There is no New3DS model for CHN/TWN

# N3DS (post5)
python exp.py usa new
python exp.py eur new
python exp.py jpn new
python exp.py kor new

# O3DS (post5)
python exp.py usa old post5
python exp.py eur old post5
python exp.py jpn old post5
python exp.py kor old post5
python exp.py chn old post5
python exp.py twn old post5

# O3DS (v3xand4x)
python exp.py usa old v3xand4x
python exp.py eur old v3xand4x
python exp.py jpn old v3xand4x
python exp.py kor old v3xand4x
python exp.py chn old v3xand4x
python exp.py twn old v3xand4x

# O3DS (v21and22)
python exp.py usa old v21and22
python exp.py eur old v21and22
python exp.py jpn old v21and22

# O3DS (pre21)
python exp.py usa old pre21
python exp.py eur old pre21
python exp.py jpn old pre21
