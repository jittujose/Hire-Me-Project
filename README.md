# Hire Me Platform

## Overview

The "Hire Me" platform is a cloud-based web application designed to connect users with temporary freelance workers, such as electricians, plumbers, and other professionals. The platform features both immediate hiring and job posting with a bidding system. It leverages blockchain technology for secure payments and uses modern web technologies for seamless performance.

## Features

### Admin Role
- **Employee Registration Management:** Review and approve or reject new employee registrations.
- **Document Verification:** Download and review certificates uploaded by employees.
- **Approval or Rejection:** Manage employee status based on registration details and document validation.

### Employee Role
- **Account Management:** Sign up or log in to the platform. New employees must complete registration and upload relevant certificates.
- **Work Activation:** Use the "Activate" button to indicate availability. This action collects the employee’s location for job matching.
- **Job Requests:** View and accept hiring requests, confirm job locations via OTP, and start work.
- **Payment Options:** Choose between cash in hand or G2 coin transfer for payment. The "Deactivate" button hides the employee’s availability when not working.
- **Job Bidding:** View job postings, place bids, and manage awarded jobs from the home page.

### User Role
- **Account Management:** Sign up or log in with a username.
- **Immediate Hiring:** Search for available workers based on location and field of work. Confirm the worker's arrival using OTP and start the work timer.
- **Job Posting:** Post non-urgent jobs with details and maximum budget. View bids and select a worker from the bidding list.
- **Payment and Rating:** Make payments using G2 tokens or directly, and rate the worker upon completion of the job.

## Technologies Used

- **Backend:** FastAPI - A modern, fast (high-performance) web framework for building APIs with Python 3.7+.
- **Storage:** Google Firestore - A flexible, scalable database for mobile, web, and server development.
- **Blockchain:** Ethereum - A decentralized platform for building smart contracts and dApps.
- **Crypto Token:** **G2 Token** - A custom cryptocurrency developed on the Ethereum platform. The G2 token is used within the platform to facilitate secure and transparent transactions between users and workers. It operates using a Solidity smart contract and is compatible with Ethereum-based wallets like MetaMask.
- **Wallet Integration:** MetaMask - A browser extension that allows users to manage their Ethereum wallet and interact with the G2 token.

## G2 Token Details

The **G2 Token** is an ERC-20 token created on the Ethereum blockchain. It serves as a payment method on the "Hire Me" platform, offering a secure and efficient way to transact between users and temporary freelance workers. The token is implemented using a Solidity smart contract, ensuring transparency and reliability in all transactions. Users can manage their G2 tokens using MetaMask, which facilitates easy and secure token transfers. Currently deployed to Polygon testnet.


