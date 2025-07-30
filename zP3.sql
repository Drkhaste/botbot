-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 11, 2025 at 06:01 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `zP3`
--

-- --------------------------------------------------------

--
-- Table structure for table `API`
--

CREATE TABLE `API` (
  `Id` int(11) NOT NULL,
  `API_Hash` longtext NOT NULL,
  `API_ID` longtext NOT NULL,
  `Name` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `API`
--

INSERT INTO `API` (`Id`, `API_Hash`, `API_ID`, `Name`) VALUES
(9, '8c9dbfe58437d1739540f5d53c72ae4b', '16623', 'PlusGram');

-- --------------------------------------------------------

--
-- Table structure for table `Devices`
--

CREATE TABLE `Devices` (
  `Id` int(11) NOT NULL,
  `Name` longtext NOT NULL,
  `OSV` longtext NOT NULL,
  `AppV` longtext NOT NULL,
  `API` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `Devices`
--

INSERT INTO `Devices` (`Id`, `Name`, `OSV`, `AppV`, `API`) VALUES
(1, 'HP Victus', 'Windows 11 x64', '5.9.2', '1'),
(2, 'Samsung Galaxy S24 Ultra', '14', '11.5.5', '2'),
(3, 'Vivo X90', '14', '10.7.5', '3'),
(4, 'Samsung Galaxy Tab S8 Ultra', '12', '10.9.1', '9'),
(5, 'iPhone 14 Pro Max', 'iOS 17', '11.5.2', '5'),
(6, 'OnePlus Nord CE 3', '13', '10.8.2', '9'),
(7, 'iPhone 11 Pro', 'iOS 15', '10.7.5', '7'),
(8, 'Google Pixel 6a', '14', '10.9.1', '9'),
(9, 'Samsung Galaxy S23 Ultra', '14', '11.4.5', '2'),
(10, 'Samsung Galaxy S23 Ultra', '14', '11.4.5', '9'),
(11, 'Samsung Galaxy S24 Ultra', '14', '11.5.5', '9');

-- --------------------------------------------------------

--
-- Table structure for table `History`
--

CREATE TABLE `History` (
  `Id` int(11) NOT NULL,
  `MID` longtext NOT NULL,
  `Peer` longtext NOT NULL,
  `AID` longtext NOT NULL,
  `TID` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Messages`
--

CREATE TABLE `Messages` (
  `Id` int(11) NOT NULL,
  `Name` longtext NOT NULL,
  `Display` longtext NOT NULL,
  `Type` longtext NOT NULL,
  `Text` longtext NOT NULL,
  `Media` longtext NOT NULL,
  `User` longtext NOT NULL,
  `Session` int(11) NOT NULL,
  `MID` longtext NOT NULL,
  `RMID` longtext NOT NULL,
  `Ti` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Queue`
--

CREATE TABLE `Queue` (
  `Id` int(11) NOT NULL,
  `TID` longtext NOT NULL,
  `SID` longtext NOT NULL,
  `Peer` longtext NOT NULL,
  `MID` longtext NOT NULL,
  `STi` longtext NOT NULL,
  `User` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Sessions`
--

CREATE TABLE `Sessions` (
  `Id` int(11) NOT NULL,
  `Name` longtext NOT NULL,
  `API_ID` longtext NOT NULL,
  `API_Hash` longtext NOT NULL,
  `Phone` longtext NOT NULL,
  `Device_Model` longtext NOT NULL,
  `System_Version` longtext NOT NULL,
  `App_Version` longtext NOT NULL,
  `Proxy` longtext NOT NULL,
  `User` longtext NOT NULL,
  `Hash` longtext NOT NULL,
  `Status` longtext NOT NULL,
  `NID` longtext NOT NULL,
  `SSession` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `SessionsB`
--

CREATE TABLE `SessionsB` (
  `Id` int(11) NOT NULL,
  `Name` longtext NOT NULL,
  `API_ID` longtext NOT NULL,
  `API_Hash` longtext NOT NULL,
  `Phone` longtext NOT NULL,
  `Device_Model` longtext NOT NULL,
  `System_Version` longtext NOT NULL,
  `App_Version` longtext NOT NULL,
  `Proxy` longtext NOT NULL,
  `User` longtext NOT NULL,
  `Hash` longtext NOT NULL,
  `Status` longtext NOT NULL,
  `NID` longtext NOT NULL,
  `SSession` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Tasks`
--

CREATE TABLE `Tasks` (
  `Id` int(11) NOT NULL,
  `Name` longtext NOT NULL,
  `Sessions` longtext NOT NULL,
  `Messages` longtext NOT NULL,
  `Peers` longtext NOT NULL,
  `Create_Ti` longtext NOT NULL,
  `RunTime` int(11) NOT NULL,
  `User` longtext NOT NULL,
  `Sleep` int(11) NOT NULL,
  `Status` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Timer`
--

CREATE TABLE `Timer` (
  `Id` int(11) NOT NULL,
  `TID` longtext NOT NULL,
  `SH` longtext NOT NULL,
  `SHT` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `Users`
--

CREATE TABLE `Users` (
  `Id` int(11) NOT NULL,
  `User` longtext NOT NULL,
  `Step` longtext NOT NULL,
  `Ti` longtext NOT NULL,
  `Data` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `Users`
--

INSERT INTO `Users` (`Id`, `User`, `Step`, `Ti`, `Data`) VALUES
(1, '609406239', 'none', '1746923571.5612965', '{\"Sessions\": [\"0\"], \"Messages\": [\"Pro1\"], \"Peers\": [], \"Sleep\": 0}');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `API`
--
ALTER TABLE `API`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `Devices`
--
ALTER TABLE `Devices`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `History`
--
ALTER TABLE `History`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `Messages`
--
ALTER TABLE `Messages`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `Queue`
--
ALTER TABLE `Queue`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `Sessions`
--
ALTER TABLE `Sessions`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `SessionsB`
--
ALTER TABLE `SessionsB`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `Tasks`
--
ALTER TABLE `Tasks`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `Timer`
--
ALTER TABLE `Timer`
  ADD PRIMARY KEY (`Id`);

--
-- Indexes for table `Users`
--
ALTER TABLE `Users`
  ADD PRIMARY KEY (`Id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `API`
--
ALTER TABLE `API`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `Devices`
--
ALTER TABLE `Devices`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `History`
--
ALTER TABLE `History`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- AUTO_INCREMENT for table `Messages`
--
ALTER TABLE `Messages`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `Queue`
--
ALTER TABLE `Queue`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- AUTO_INCREMENT for table `Sessions`
--
ALTER TABLE `Sessions`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `SessionsB`
--
ALTER TABLE `SessionsB`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `Tasks`
--
ALTER TABLE `Tasks`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `Timer`
--
ALTER TABLE `Timer`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `Users`
--
ALTER TABLE `Users`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
