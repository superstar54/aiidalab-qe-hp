====================================
How to calculate Hubbard parameters
====================================

Overview
========
This tutorial will guide you through the process of setting up and running Hubbard parameters calculation for LiCoO2.


Steps
=====

To start, go ahead and :doc:`launch </installation/launch>` the app, then follow the steps below.


Step 1 Select a structure
--------------------------------
For this tutorial task, please use the `From Examples` tab, and select the LiCoO2 structure.

Click the `Confirm` button to proceed.

.. figure:: /_static/images/hp_step_1.png
   :align: center


Step 2 Configure workflow
--------------------------------

In the **Basic Settings** tab, set the following parameters:

- In the **Structure optimization** section, select ``Structure as is``.
- Set **Electronic Type** to ``Insulator``
- In the **properties** section, select ``Habbard parameter (HP)``


Then go to the **HP setting** tab and, in the **Hubbard U** section, select ``Co`` by ticking the appropriate box.
Set the **Manifold** to ``3d``.
In the **Hubbard V** section, select first row by ticking the appropriate box.
Set the **Manifold** to ``3d`` and ``2p`` for the **Co** atom and **O** atom, respectively.

.. image:: ../_static/images/hp_step_2_setting_tab.png
   :align: center


Click the **Confirm** button to proceed.


Step 3 Choose computational resources
---------------------------------------
In this small system, we can use the default `localhost` computer to run the calculation.


.. tip::
   For large system, we need the high-performance computer to run HP calculation.
   Please read the relevant :doc:`How-To </howto/setup_computer_code>` section to setup code on a remote machine.

Set the number of CPUs/nodde to 2.


.. image:: ../_static/images/hp_step_3.png
   :align: center


Then, click the **Submit** button.



Step 4 Check the status and results
-----------------------------------------
The job may take 5~10 minutes to finish.

While the calculation is running, you can monitor its status as shown in the :ref:`basic tutorial <basic_status>`.
When the job is finished, you can view result spectra in the `HP` tab.

.. tip::

   If the `HP` tab is now shown when the jobs is finished.
   Click the ``QeAppWorkChain<pk>`` item on top of the nodetree to refresh the step.

Here is the result of the HP calculation.


.. figure:: /_static/images/hp_step_4_xps_tab.png
   :align: center


Congratulations, you have finished this tutorial!


Another example
====================
NiO is another example of a material that can be used to calculate Hubbard parameters.


Questions
=========

If you have any questions, please, do not hesitate to ask on the AiiDA discourse forum: https://aiida.discourse.group/.
