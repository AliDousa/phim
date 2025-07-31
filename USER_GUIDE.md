# Public Health Intelligence Platform - User Guide

**Version:** 1.0.0  
**Author:** Manus AI  
**Date:** June 8, 2025  

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation on Windows](#installation-on-windows)
3. [First Steps](#first-steps)
4. [Dashboard Overview](#dashboard-overview)
5. [Managing Datasets](#managing-datasets)
6. [Running Simulations](#running-simulations)
7. [Data Visualization](#data-visualization)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Getting Started

The Public Health Intelligence Platform is a comprehensive tool designed for epidemiologists, public health researchers, and data scientists to analyze disease spread patterns, run predictive models, and visualize public health data. This platform combines advanced machine learning algorithms with traditional epidemiological models to provide insights into disease transmission dynamics.

### What You Can Do

With this platform, you can perform sophisticated epidemiological analysis including SEIR compartmental modeling, agent-based simulations, network-based transmission modeling, and machine learning forecasting. The platform supports time-series analysis, spatial data visualization, and real-time monitoring of disease spread patterns. Whether you're tracking seasonal flu patterns, analyzing pandemic responses, or forecasting disease outbreaks, this platform provides the tools and computational power needed for comprehensive public health intelligence.

### System Requirements

Before installation, ensure your Windows system meets the minimum requirements. You'll need Windows 10 or later with at least 4GB of RAM, though 8GB is recommended for large simulations. The platform requires approximately 2GB of disk space for installation and additional space for datasets and simulation results. A stable internet connection is needed for initial setup and any external data sources you may want to integrate.

## Installation on Windows

The platform has been specifically optimized for Windows environments with automated setup scripts that handle all dependencies and configuration. The installation process is designed to be straightforward, requiring minimal technical expertise while ensuring all components are properly configured for optimal performance.

### Quick Installation

The fastest way to get started is using the automated setup script. Download the complete project folder to your desired location on your Windows machine. Navigate to the project directory and locate the `setup-windows.bat` file. Right-click on this file and select "Run as administrator" to ensure proper permissions for installing dependencies.

The setup script will automatically check for required prerequisites including Python 3.11 or later and Node.js 18 or later. If these are not installed, the script will provide download links and pause to allow you to install them. Once prerequisites are confirmed, the script creates Python virtual environments, installs all required packages, sets up the database, and creates convenient startup scripts for launching the platform.

### Manual Installation Steps

If you prefer manual installation or encounter issues with the automated script, you can install components individually. First, ensure Python 3.11+ is installed and accessible from the command line. Open Command Prompt and verify by running `python --version`. Next, install Node.js 18+ from the official website and verify with `node --version`.

Navigate to the backend directory and create a virtual environment using `python -m venv venv`. Activate the environment with `venv\Scripts\activate.bat` and install dependencies using `pip install -r requirements.txt`. For the frontend, navigate to the frontend directory and run `npm install` to install all JavaScript dependencies.

### Verifying Installation

After installation, verify everything is working correctly by running the integration test script. Open Command Prompt in the project root directory and execute `python integration_test.py`. This script checks all components, verifies file integrity, and confirms that both backend and frontend can be built successfully. A successful test run indicates your installation is complete and ready for use.

## First Steps

Once installation is complete, launching the platform is straightforward using the provided startup scripts. These scripts handle the coordination between backend and frontend services, ensuring they start in the correct order and with proper configuration.

### Starting the Platform

To launch the complete platform, double-click the `start-platform.bat` file in the project root directory. This script opens two command windows: one for the backend API server and another for the frontend React application. The backend typically starts on port 5000, while the frontend development server uses port 5173. Wait for both services to fully initialize before proceeding.

Alternatively, you can start services individually using `start-backend.bat` and `start-frontend.bat` if you need more control over the startup process or want to monitor each service separately. This approach is useful for development or troubleshooting purposes.

### Accessing the Application

Once both services are running, open your web browser and navigate to `http://localhost:5173`. You should see the Public Health Intelligence Platform login screen. The modern, professional interface is designed for ease of use while providing access to powerful analytical capabilities.

### Creating Your Account

Click the "Register" tab to create your first user account. Provide a unique username, valid email address, and secure password. Optionally, include your full name and organization for better collaboration and data tracking. The platform supports different user roles including Analyst, Researcher, and Administrator, each with appropriate permissions for their responsibilities.

After successful registration, you'll be automatically logged in and redirected to the main dashboard. The dashboard provides an overview of your activities, quick access to common functions, and real-time status information about your simulations and datasets.

## Dashboard Overview

The dashboard serves as your central command center for all platform activities. The interface is designed with a clean, modern aesthetic that prioritizes functionality while remaining visually appealing. The layout adapts to different screen sizes, ensuring usability on both desktop and tablet devices.

### Navigation Structure

The left sidebar provides primary navigation with clearly labeled sections for different platform functions. The Dashboard section offers an overview of your activities and quick access to common tasks. The Analytics section houses the comprehensive data visualization tools with interactive charts and graphs. The Datasets section manages your uploaded data files and their validation status. The Simulations section controls your epidemiological models and their execution. The Monitoring section provides real-time status updates and system health information. Finally, the Settings section allows customization of your preferences and account management.

### Main Content Area

The central content area adapts based on your current section, providing relevant tools and information. In the Dashboard view, you'll see summary statistics including total datasets, active simulations, completed analyses, and recent forecasts. These metrics provide quick insight into your platform usage and productivity.

The Recent Activity panel shows chronological updates from your simulations and datasets, helping you track progress and identify completed tasks. The Quick Actions panel provides one-click access to common operations like uploading new datasets, creating SEIR simulations, generating forecasts, and viewing analytics.

### Status Indicators
Throughout the interface, status indicators provide immediate feedback about system state and operation progress. This is especially useful for tracking simulations, which now run as background tasks.
- **Pending**: The simulation is in the queue waiting to be processed.
- **Running**: The simulation is actively being processed by a worker.
- **Completed**: The simulation finished successfully, and results are available.
- **Failed**: The simulation encountered an error. You can view the error details for troubleshooting.

## Managing Datasets

Effective dataset management is crucial for meaningful epidemiological analysis. The platform supports various data formats and provides comprehensive tools for validation, organization, and quality assessment.

### Supported Data Formats

The platform accepts CSV and JSON files containing epidemiological data. For time-series data, ensure your files include date columns in standard formats (YYYY-MM-DD or MM/DD/YYYY). Spatial data should include location identifiers such as region names, postal codes, or geographic coordinates. Cross-sectional data can include demographic breakdowns, survey responses, or snapshot measurements.

### Uploading Datasets

To upload a new dataset, navigate to the Datasets section and click "Upload New Dataset." Select your data file and provide descriptive metadata including a meaningful name, detailed description, data type classification, and source information. This metadata helps organize your datasets and enables better collaboration with team members.

The platform performs an initial validation on your file to check for correct format (CSV, JSON, XLSX) and size. After you confirm the upload and map your columns, the platform processes and validates the data content in the background. You can monitor the validation status in the Datasets list.

### Data Validation and Quality

The background validation process examines data structure, completeness, and consistency. For time-series data, the system checks for chronological ordering, identifies gaps in the timeline, and flags unusual patterns that might indicate data quality issues. Spatial data validation ensures location identifiers are consistent and recognizable.

When validation issues are detected, the platform provides specific guidance for resolution. Common issues include inconsistent date formats, missing geographic identifiers, or outlier values that may represent data entry errors. The platform suggests corrections while preserving your original data integrity.

### Organizing Your Data

As your dataset collection grows, organization becomes increasingly important. Use descriptive names that include key characteristics like geographic scope, time period, and data source. The platform provides filtering and search capabilities to help locate specific datasets quickly.

Consider creating a consistent naming convention for your organization. For example, "COVID19_Regional_2020-2025_HealthDept" clearly indicates the disease, geographic scope, time period, and data source. This approach facilitates collaboration and reduces confusion when working with multiple datasets.

## Running Simulations

The platform offers several sophisticated epidemiological models, each suited for different types of analysis and research questions. When you start a simulation, it is processed asynchronously in the background. This means you don't have to wait for it to finish and can continue using the platform or even close your browser. You can monitor the real-time status of your simulations on the dashboard.

### SEIR Compartmental Models

The SEIR (Susceptible-Exposed-Infectious-Recovered) model is the foundation of epidemiological modeling, dividing populations into distinct compartments based on disease status. This model is particularly effective for analyzing diseases with known incubation periods and well-characterized transmission dynamics.

To create a SEIR simulation, select your validated dataset and specify key parameters including the transmission rate (beta), incubation rate (sigma), and recovery rate (gamma). The platform provides guidance for parameter selection based on published literature and your specific disease context. Population size should match your dataset scope, whether analyzing a city, region, or entire country.

The SEIR model excels at predicting epidemic peaks, estimating total attack rates, and evaluating intervention effectiveness. Results include time-series projections for each compartment, key metrics like R0 (basic reproduction number), and summary statistics about epidemic characteristics.

### Agent-Based Modeling

Agent-based models simulate individual agents (people) and their interactions, providing detailed insights into how individual behaviors affect population-level outcomes. This approach is particularly valuable for analyzing heterogeneous populations or evaluating targeted interventions.

When configuring agent-based simulations, consider population demographics, contact patterns, and behavioral variations. The platform allows specification of age groups, activity levels, and compliance rates for different population segments. These parameters significantly influence model outcomes and should reflect your study population characteristics.

Agent-based models require more computational resources than compartmental models but provide richer insights into transmission dynamics. Results include individual-level outcomes, spatial spread patterns, and detailed analysis of intervention effectiveness across different population groups.

### Network-Based Models

Network models represent social connections explicitly, modeling disease transmission through defined relationship structures. This approach is ideal for analyzing diseases that spread through specific contact networks or for evaluating interventions that target network properties.

Network model configuration requires defining connection patterns, contact frequencies, and network topology. The platform supports various network structures including random networks, small-world networks, and scale-free networks. Choose the structure that best represents your study population's social organization.

These models excel at identifying super-spreader events, analyzing cluster formation, and evaluating network-based interventions like contact tracing or targeted vaccination. Results include network visualizations, transmission pathway analysis, and metrics about network efficiency and vulnerability.

### Machine Learning Forecasting

The platform's machine learning capabilities combine multiple algorithms to generate robust forecasts with uncertainty quantification. This approach is particularly valuable for short-term predictions and when traditional epidemiological models may not capture all relevant factors.

Machine learning models automatically select relevant features from your dataset, including temporal patterns, seasonal effects, and external variables. The ensemble approach combines Random Forest, Gradient Boosting, and Linear models to provide robust predictions with confidence intervals.

These models are especially effective for operational planning, resource allocation, and early warning systems. Results include point forecasts, prediction intervals, and feature importance analysis that helps identify key drivers of disease transmission.

### Simulation Management

The platform provides comprehensive tools for managing simulation workflows. The Simulations dashboard shows all your analyses with real-time status indicators (`Pending`, `Running`, `Completed`, `Failed`), completion times, and summary results. The list updates automatically as simulations progress, so you always have the latest information. You can easily compare different scenarios, track parameter sensitivity, and organize related simulations.

If a simulation fails, the status will change to `Failed`, and you can click on it to view the error details, which can help in troubleshooting the issue with your parameters or dataset.

## Data Visualization

The platform's visualization capabilities transform complex epidemiological data into clear, actionable insights. The interactive charts and graphs are designed for both exploratory analysis and professional presentation.

### Interactive Charts

The Analytics section provides comprehensive visualization tools built on modern web technologies. Charts are fully interactive, allowing zooming, panning, and detailed exploration of your data. Hover over data points to see exact values, click legend items to toggle data series, and use built-in controls to adjust time ranges or filter by categories.

SEIR model results are displayed as stacked area charts showing the evolution of each compartment over time. These visualizations clearly show epidemic progression, peak timing, and final outcomes. Color coding follows epidemiological conventions with blue for susceptible, orange for exposed, red for infectious, and green for recovered populations.

### Forecasting Visualizations

Machine learning forecasts are presented with confidence intervals that show prediction uncertainty. The charts distinguish between historical data (solid lines) and predictions (dashed lines), making it easy to understand model performance and forecast reliability. Confidence bands provide visual indication of prediction uncertainty, helping users make informed decisions based on model outputs.

Regional comparison charts use bar graphs and maps to show geographic distribution of cases, deaths, and recoveries. These visualizations help identify hotspots, track geographic spread, and evaluate regional intervention effectiveness. Interactive maps allow drilling down to specific areas for detailed analysis.

### Model Performance Metrics

The platform provides comprehensive model evaluation tools including accuracy metrics, goodness-of-fit measures, and comparison charts. These visualizations help assess model reliability and choose appropriate models for specific applications. Performance metrics are presented in clear, standardized formats that facilitate model comparison and validation.

### Customization Options

Visualization tools include extensive customization options for colors, scales, and display formats. You can adjust chart types, modify axis ranges, and select specific data series for focused analysis. Export options include high-resolution images suitable for publications and presentations, as well as data exports for external analysis tools.
Once a simulation's status is `Completed`, you can click on it to view the detailed results and interactive visualizations.

## Advanced Features

The platform includes sophisticated features for power users and specialized applications. These capabilities extend the basic functionality to support complex research workflows and advanced analytical requirements.

### Parameter Estimation

The platform includes Bayesian parameter estimation capabilities that can infer model parameters from observed data. This feature is particularly valuable when working with new diseases or populations where parameter values are uncertain. The Bayesian approach provides parameter estimates with uncertainty quantification, helping users understand the reliability of their model inputs.

To use parameter estimation, provide observed data and specify prior distributions for unknown parameters. The platform uses advanced sampling algorithms to explore parameter space and identify values that best explain your data. Results include posterior distributions for each parameter, convergence diagnostics, and model fit assessments.

### Ensemble Modeling

For maximum robustness, the platform supports ensemble approaches that combine multiple models or parameter sets. Ensemble methods reduce prediction uncertainty and provide more reliable forecasts by averaging across different model assumptions. This approach is particularly valuable for policy-relevant applications where decision-makers need robust predictions.

Ensemble configuration allows weighting different models based on their historical performance or theoretical appropriateness. The platform automatically tracks ensemble performance and adjusts weights based on ongoing validation against new data.

### Sensitivity Analysis

Understanding how model outputs respond to parameter changes is crucial for reliable epidemiological analysis. The platform provides comprehensive sensitivity analysis tools that systematically vary parameters and assess output sensitivity. These analyses help identify critical parameters, understand model behavior, and assess prediction robustness.

Sensitivity analysis results are presented as tornado plots, parameter sweep visualizations, and correlation matrices. These tools help users focus on the most important parameters and understand the sources of prediction uncertainty.

### Batch Processing

For systematic analysis of multiple scenarios or parameter combinations, the platform supports batch processing capabilities. Users can define parameter ranges, specify output requirements, and submit multiple simulations for automated execution. This feature is particularly valuable for policy analysis, intervention evaluation, and systematic model validation.

Batch results are automatically organized and summarized, with tools for comparing outcomes across different scenarios. The platform provides statistical summaries, visualization tools, and export capabilities for comprehensive analysis of batch results.

### API Integration

Advanced users can access platform capabilities through the comprehensive REST API. This enables integration with external tools, automated workflows, and custom applications. The API supports all platform functions including data upload, simulation management, and result retrieval.

API documentation includes detailed examples, SDK libraries for popular programming languages, and authentication guidance. This enables seamless integration with existing research workflows and institutional systems.

## Troubleshooting

While the platform is designed for reliability and ease of use, occasional issues may arise. This section provides guidance for identifying and resolving common problems.

### Installation Issues

If the automated setup script fails, first verify that Python and Node.js are properly installed and accessible from the command line. Check that you have administrative privileges and that antivirus software isn't blocking the installation process. Windows Defender or other security software may flag the installation scripts as potentially harmful due to their system modification capabilities.

For permission-related issues, try running the setup script as administrator. If specific packages fail to install, check your internet connection and consider using alternative package repositories. The platform includes fallback installation methods for common connectivity issues.

### Startup Problems

If the platform fails to start, check that the required ports (5000 for backend, 5173 for frontend) are not being used by other applications. Use the Windows Task Manager to identify and close conflicting processes. Firewall settings may also block the required network connections, so ensure the platform is allowed through Windows Firewall.

Database initialization errors often indicate file permission issues or insufficient disk space. Ensure the platform directory has write permissions and adequate free space for database files and temporary storage.

### Performance Issues

Simulations now run in the background, so they will not slow down the user interface. If a simulation is in the `Running` state for an unexpectedly long time, it may be due to a very large dataset or complex parameters. If a simulation `Fails`, check the error message for details. Common causes include invalid parameters or issues with the input dataset.

Memory issues may occur with very large datasets or complex simulations. Close unnecessary applications and consider upgrading system RAM if you regularly work with large-scale analyses. The platform provides memory usage monitoring to help identify resource constraints.

### Data Import Problems

Dataset validation failures often result from formatting inconsistencies or missing required fields. Review the error messages carefully and compare your data format to the provided examples. Common issues include inconsistent date formats, missing headers, or unexpected character encodings.

For large datasets, upload timeouts may occur with slow internet connections. Consider splitting large files into smaller chunks or using a more reliable network connection. The platform supports resumable uploads for improved reliability with large files.

### Visualization Issues

If charts fail to display or appear corrupted, try refreshing your browser or clearing the browser cache. Ensure you're using a modern browser with JavaScript enabled. Some visualization features require WebGL support, which may not be available on older systems or with certain graphics drivers.

Export functionality may fail with very large datasets or complex visualizations. Try reducing the data range or simplifying the visualization before exporting. The platform provides multiple export formats to accommodate different requirements and system capabilities.

## Best Practices

Effective use of the Public Health Intelligence Platform requires understanding both the technical capabilities and the epidemiological principles underlying the models. Following established best practices ensures reliable results and meaningful insights.

### Data Quality Management

High-quality input data is essential for meaningful epidemiological analysis. Before uploading datasets, carefully review data completeness, accuracy, and consistency. Remove or flag obvious outliers, ensure date formats are consistent, and verify that geographic identifiers are standardized. Document any data cleaning steps for reproducibility and transparency.

Maintain detailed metadata for all datasets including data sources, collection methods, geographic scope, and temporal coverage. This information is crucial for proper model interpretation and enables other researchers to understand and build upon your work.

### Model Selection Guidelines

Choose models based on your research questions, available data, and computational resources. SEIR models are ideal for population-level analysis and policy evaluation. Agent-based models provide detailed insights into individual behaviors and heterogeneous populations. Network models excel at analyzing transmission through specific contact structures. Machine learning approaches are valuable for short-term forecasting and when traditional models may miss important patterns.

Consider model complexity relative to your data quality and quantity. Simple models with well-estimated parameters often outperform complex models with uncertain inputs. Start with basic models and add complexity only when justified by improved performance or specific research requirements.

### Parameter Selection

Use published literature, expert knowledge, and data-driven estimation to select appropriate model parameters. Document parameter sources and rationale for transparency and reproducibility. When parameter uncertainty is high, use sensitivity analysis to understand how uncertainty affects your conclusions.

For diseases with limited parameter information, consider using parameter estimation features to infer values from your data. Bayesian approaches provide uncertainty quantification that helps assess parameter reliability and model confidence.

### Validation and Verification

Always validate model outputs against known data or expert expectations. Compare predictions to historical outcomes when possible, and assess whether model behavior aligns with epidemiological theory. Use cross-validation techniques to evaluate predictive performance and identify potential overfitting.

Document validation procedures and results for transparency and reproducibility. Consider external validation using independent datasets when available. Validation is an ongoing process that should continue as new data becomes available.

### Collaboration and Sharing

The platform supports collaborative research through user management and data sharing capabilities. Establish clear protocols for data access, model sharing, and result interpretation within your research team. Use consistent naming conventions and documentation standards to facilitate collaboration.

Consider publishing model specifications, parameter values, and validation results to support reproducible research. The platform's export capabilities facilitate sharing with external collaborators and integration with publication workflows.

### Continuous Learning

Epidemiological modeling is a rapidly evolving field with new methods, data sources, and applications emerging regularly. Stay current with literature, attend relevant conferences, and participate in professional networks. The platform's flexibility allows incorporation of new approaches as they become available.

Regularly review and update your modeling practices based on new evidence and methodological developments. Consider participating in model comparison exercises and validation studies to benchmark your approaches against community standards.

---

This user guide provides comprehensive guidance for effective use of the Public Health Intelligence Platform. For additional support, consult the API documentation, contact the development team, or participate in the user community forums. The platform is designed to evolve with user needs and epidemiological research advances, ensuring continued relevance and utility for public health intelligence applications.
