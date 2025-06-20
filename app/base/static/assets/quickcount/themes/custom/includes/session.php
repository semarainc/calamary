<?php
	include 'themes/custom/includes/conn.php';
	session_start();

	//voters here means email
	//for candidate
	if(isset($_SESSION['voter'])){
		$sql = "SELECT * FROM data_pemilih WHERE nik = '".$_SESSION['voter']."'";
		$query = $conn->query($sql);
		$voter = $query->fetch_assoc();
	}
	else{
		header('location: voters.php');
		exit();
	}

?>