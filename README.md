anel_power_control
==================

Python library for the AJAX interface provided by Anel Power Control Home/Pro.

Example
-------

    from anel_power_control import AnelPowerControl

    ctrl = AnelPowerControl('hostname', auth=('user', 'pass'))

    print(ctrl[0])

    print(ctrl.temperature)

    print(ctrl['My Socket'].is_on)

    ctrl['My Socket'].on()

    print(ctrl['My Socket'].is_on)

    ctrl['My Socket'].off()
    
    print(ctrl['My Socket'].is_on)

