# milksense

The MilkSense analytics
component provides real-time estimation of the microbial load on a given Bulk
Milk Containers (BMCs), based on the information collected from Infoscope’s
Meton devicees and retrieved via the Meterscope platform. The calculation
relies on the previous estimations of microbial load and the identification of
status change on the BMC (lid opened/closed, new milk bulk loaded to the BMC.



In more detail, the model estimates
the concentration of Colony Forming Units per millilitre of milk (CFU/ml) by
associating CFU/ml with temperature and timespan of preservation. The
methodology for building the model is summarised in the following steps: 



1.    Estimate the trajectory of CFU at a
standard temperature



2.    Estimate the impact of temperature by
correlating the trajectories in different temperatures



3.    Extrapolate the evolution of CFU in
different time intervals than the ones originally available and specifically
5-minute intervals



4.    Combine the observations in order to
produce a formula that calculates the CFU at the next timepoint given that the
temperature is known for the specific and previous timepoints.



The produced formula and the workflow for computing
CFU/ml is depicted in Figure 1, where the temperature TEMP is set as the
average of the current and previous measurement, and the  and  factors are
computed based on the previous CFU/ml measurement).
